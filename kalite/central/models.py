import random
import datetime
from collections import OrderedDict

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
    owner = models.ForeignKey(User, related_name="owned_organizations", null=True)

    HEADLESS_ORG_NAME = "Headless Zones"
    HEADLESS_ORG_PK = None  # keep the primary key of the headless org around, for efficiency
    HEADLESS_ORG_SAVE_FLAG = "internally_safe_headless_org_save"  # indicates safe save() call


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
        # backwards compatibility
        if not getattr(self, "owner_id", None):
            self.owner = owner
            assert self.owner or self.name == Organization.HEADLESS_ORG_NAME, "Organization must have an owner (save for the 'headless' org)" 

        # Make org unique by name, for headless name only.
        #   So make sure that any save() call is coming either
        #   from a trusted source (passing HEADLESS_ORG_SAVE_FLAG),
        #   or doesn't overlap with our safe name
        if self.name == Organization.HEADLESS_ORG_NAME and not kwargs.get(Organization.HEADLESS_ORG_SAVE_FLAG, False):
            headless_org = Organization.get_headless_organization()
            if headless_org.pk != self.pk:
                raise Exception("Cannot add more than one headless org!")
        super(Organization, self).save(*args, **kwargs)


    @classmethod
    def from_zone(cls, zone):
        """
        Given a zone, figure out which organizations contain it.
        """
        return Organization.objects.filter(zones__pk=zone.pk)


    @classmethod
    def get_headless_organization(cls, user):
        assert user.is_superuser, "only super-users can call this method!"

        if cls.HEADLESS_ORG_PK is not None:
            # Already exists and cached, just query fast and return
            org = cls.objects.get(pk=cls.HEADLESS_ORG_PK)
            return org

        else:
            # Potentially inefficient query, so limit this to once per server thread
            # by caching the results.  Here, we've had a cache miss
            orgs = cls.objects.filter(name=cls.HEADLESS_ORG_NAME)
            if not orgs:
                # Cache miss because the org actually doesn't exist.  Create it!
                org = Organization(name=cls.HEADLESS_ORG_NAME, owner=user)
                org.save(**({cls.HEADLESS_ORG_SAVE_FLAG: True}))
                cls.HEADLESS_ORG_PK = org.pk
                return org
            else:
                # Cache miss because it's the first relevant query since this thread started.
                assert len(orgs) == 1, "Cannot have multiple HEADLESS ZONE organizations"
                cls.HEADLESS_ORG_PK = orgs[0].pk
                return orgs[0]


    @classmethod
    def update_headless_organization(cls, user):
        assert user.is_superuser, "only super-users can call this method!"
        headless_org = Organization.get_headless_organization(user)
        headless_zones = Zone.get_headless_zones()
        if headless_zones:
            for zone in headless_zones:
                headless_org.zones.add(zone)
            headless_org.save()
        return headless_org


class UserProfile(models.Model):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        orgs = OrderedDict()  # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all():  # add in order queries (alphabetical?)
            orgs[org.pk] = org

        # Add a headless organization for superusers, containing
        #   any headless zones.
        # Make sure this is at the END of the list, so it is clearly special.
        if self.user.is_superuser:
            headless_org = Organization.update_headless_organization(self.user)
            if headless_org.zones:
                orgs[headless_org.pk] = headless_org

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
            'central_server_host': request.META.get('HTTP_HOST', settings.CENTRAL_SERVER_HOST),  # for central server actions, determine DYNAMICALLY to be safe

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

