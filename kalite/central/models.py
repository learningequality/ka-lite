import collections
import random
import datetime

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

import settings
from securesync import crypto
from securesync.models import Zone


def get_or_create_user_profile(user):
    assert not user.is_anonymous(), "Should not be calling get_or_create_user_profile with an anonymous user."
    assert user.is_authenticated(), "Should not be calling get_or_create_user_profile with an anonymous user."
    
    return UserProfile.objects.get_or_create(user=user)[0]

class Organization(models.Model):
    name = models.CharField(verbose_name="org name", max_length=100)
    description = models.TextField(help_text="<br/>How is this organization using KA Lite?", blank=True, )
    url = models.URLField(verbose_name="org URL", help_text="<br/>(optional)", blank=True)
    number = models.CharField(verbose_name="phone", max_length=100, blank=True)
    address = models.TextField(max_length=200, help_text="<br/>Street Address or PO Box, City/Town/Province, Postal Code", blank=True)
    country = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(User)
    zones = models.ManyToManyField(Zone)
    owner = models.ForeignKey(User, related_name="owned_organizations")

    dummy_name = "Headless Zones"
    
    def get_zones(self):
        return list(self.zones.all())

    def add_member(self, user):
        return self.users.add(user)

    def get_members(self):
        return list(self.users.all())

    def is_member(self, user):
        return self.users.filter(pk=user.pk).count() > 0

    def __unicode__(self):
        return self.name

    def save(self, owner=None, *args, **kwargs):
        if not self.owner_id:
            self.owner = owner
            
        # Make org unique by name, for dummy name only.
        if self.name==Organization.dummy_name:
            dummy_orgs = Organization.objects.filter(name=Organization.dummy_name)
            if len(dummy_orgs)>0 and self.pk not in [d.pk for d in dummy_orgs]:
                raise Exception("Cannot add more than one dummy org!")
                
        super(Organization, self).save(*args, **kwargs)

    @classmethod
    def from_zone(cls, zone):
        """Given a zone, figure out which organization is the parent."""
    
        return Organization.objects.filter(zones__pk=zone.pk)
    
    @classmethod
    def get_dummy_organization(cls, user):
        assert user.is_superuser, "only super-users can call this method!"
        
        orgs = cls.objects.filter(name=cls.dummy_name)
        if not orgs:
            org = Organization(name=cls.dummy_name, owner=user)
            org.save()
            return org
        else:
            assert len(orgs)==1, "Cannot have multiple dummy organizations"
            return orgs[0]
        
    @classmethod
    def update_dummy_organization(cls, user):
        assert user.is_superuser, "only super-users can call this method!"
        dummy_org = Organization.get_dummy_organization(user)
        headless_zones = Zone.get_headless_zones()
        if headless_zones:
            for zone in headless_zones:
                dummy_org.zones.add(zone)
            dummy_org.save()
        return dummy_org
            
class UserProfile(models.Model):  
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        orgs = collections.OrderedDict() # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all():
            orgs[org.pk] = org
        
        # Add a dummy organization for superusers, containing
        #   any headless zones
        if self.user.is_superuser:
            dummy_org = Organization.update_dummy_organization(self.user)
            if dummy_org.zones:
                orgs[dummy_org.pk] = dummy_org

        return orgs

    
class OrganizationInvitation(models.Model):
    email_to_invite = models.EmailField(verbose_name="Email of invitee", max_length=75)
    invited_by = models.ForeignKey(User)
    organization = models.ForeignKey(Organization, related_name="invitations")

    class Meta:
        unique_together = ('email_to_invite', 'organization')

    def send(self, request):
        to_email = self.email_to_invite
        sender = settings.CENTRAL_FROM_EMAIL
        cdict = {
            'organization': self.organization,
            'invited_by': self.invited_by,
            'central_server_host': request.META.get('HTTP_HOST', settings.CENTRAL_SERVER_HOST), # for central server actions, determine DYNAMICALLY to be safe

        }
        # Invite an existing user
        if User.objects.filter(email=to_email).count() > 0:
            subject = render_to_string('central/org_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/org_invite_email.txt', cdict, context_instance=RequestContext(request))
        # Invite an unregistered user
        else:
            subject = render_to_string('central/central_invite_email_subject.txt', cdict, context_instance=RequestContext(request))
            body = render_to_string('central/central_invite_email.txt', cdict, context_instance=RequestContext(request))
        send_mail(subject, body, sender, [to_email], fail_silently=False)


class DeletionRecord(models.Model):
    organization = models.ForeignKey(Organization)
    deleter = models.ForeignKey(User, related_name="deletion_actor")
    deleted_user = models.ForeignKey(User, related_name="deletion_recipient", blank=True, null=True)
    deleted_invite = models.ForeignKey(OrganizationInvitation, blank=True, null=True)


class FeedListing(models.Model):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    posted_date = models.DateTimeField()
    url = models.URLField()
    
    def get_absolute_url(self):
        return self.url
    
class Subscription(models.Model):
    email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, blank=True)

