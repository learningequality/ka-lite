import random
import datetime

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.db.models import Max

import settings
from securesync import crypto
from securesync.models import Zone


def get_or_create_user_profile(user):
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
        super(Organization, self).save(*args, **kwargs)


class UserProfile(models.Model):  
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        orgs = {} # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all():
            orgs[org.pk] = org
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




class ZoneKey(models.Model):
    """Zones should have keys, but for back compat, they can't.
    So, let's define a one-to-one table, to store zone keys."""
    zone = models.ForeignKey(Zone, verbose_name=_("Zone"))
    private_key = models.TextField(max_length=500)
    public_key = models.TextField(max_length=500)
    
    key = None
    
    def save(self, *args, **kwargs):
        # Auto-generate keys, if necessary
        if not self.private_key:
            key = crypto.Key()
            self.private_key = key.get_private_key_string()
            self.public_key  = key.get_public_key_string()
        elif not self.public_key:
            self.public_key = self.get_key().get_public_key_string()
        
        super(ZoneKey, self).save(*args, **kwargs)
        
        
    def get_key(self):

        # We have a cryptographic key object (from previous run); return it
        if self.key:
            return self.key

        # We have key strings, but no key object.  create one!
        elif self.private_key:
            # For back-compatibility, where zones didn't have keys
            if self.private_key=="dummy_key":
                self.private_key = None
                self.public_key = None
                self.save()
                
            self.key = crypto.Key(private_key_string = self.private_key, public_key_string = self.public_key)
            return self.key

        else:
            # Cannot create a key here; otherwise we run the risk
            #   of changing the key (if it's generated here and not saved)
            raise Exception('No key set for this object.')
            
            
    def generate_install_certificate(self, string_to_sign=None):
        """Generates an install certificate by signing a string with
        the zone's private key.
        If no string is given, then one will be generated"""
        
        # Should have something more intelligent here
        if not string_to_sign:
            string_to_sign = "%f" % random.random()
        
        return self.get_key().sign(string_to_sign)
        
        
class ZoneOutstandingInstallCertificate(models.Model):
    """In order to auto-register with a zone, the zone can provide
    an "installation certificate"; if a valid installation certificate
    is provided by a device, the zone accepts the request to join,
    and the certificate is removed from the list of outstanding certs."""
    
    zone = models.ForeignKey(Zone, verbose_name=_("Zone"))
    device_counter = models.IntegerField()
    install_certificate = models.CharField(max_length=500)
    creation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField()
    
    
#    @transaction.atomic
    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        # Generate the certificate
        if not self.install_certificate:
            try:
                zone_key = ZoneKey.objects.get(zone=self.zone)
            except ZoneKey.DoesNotExist:
                # generate the zone key
                zone_key = ZoneKey(zone=self.zone)
                zone_key.save()
                zone_key.full_clean()
                
            self.install_certificate = zone_key.generate_install_certificate()
            
        # Expire in one year, if not specified
        if not self.expiration_date:
            if not self.creation_date:
                self.creation_date = datetime.datetime.now()
            self.expiration_date = self.creation_date + datetime.timedelta(years=1)
        
        # Device counter is the next one available.
        if not self.device_counter: 
            # danger! danger! race/concurrency conditions! 
            # added transaction decorator, but ... who knows if that protects enough :(
            # Generates a "SELECT MAX..." statement
            self.device_counter = 1+Zone.get_next_device_counter()
            
        super(ZoneOutstandingInstallCertificate, self).save(*args, **kwargs)
    
    @staticmethod
    def validate(self, install_certificate):
        """Check that the given certificate is recognized, but don't actually use it."""
        
        try:
            ZoneOutstandingInstallCertificate.get(install_certificate=install_certificate)
            return True
        except NotFoundException as e:
            return False
            
                
    def use(self):
        """Use the given install certificate: validate it, and remove it from the database.
        If the certificate was invalid/unrecognized, then the method with raise an Exception"""
        
        self.delete()