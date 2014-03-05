import random
import datetime
from collections import OrderedDict

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

import settings
from securesync.models import Zone
from utils.django_utils import ExtendedModel


def get_or_create_user_profile(user):
    assert not user.is_anonymous(), "Should not be calling get_or_create_user_profile with an anonymous user."
    assert user.is_authenticated(), "Should not be calling get_or_create_user_profile with an anonymous user."

    return UserProfile.objects.get_or_create(user=user)[0]

class Organization(ExtendedModel):
    name = models.CharField(verbose_name="org name", max_length=100)
    description = models.TextField(help_text="<br/>How is this organization using KA Lite?", blank=True, )
    url = models.URLField(verbose_name="org URL", help_text="<br/>(optional)", blank=True)
    number = models.CharField(verbose_name="phone", max_length=100, blank=True)
    address = models.TextField(max_length=200, help_text="<br/>Street Address or PO Box, City/Town/Province, Postal Code", blank=True)
    country = models.CharField(max_length=100, blank=True)
    users = models.ManyToManyField(User)
    zones = models.ManyToManyField(Zone)
    owner = models.ForeignKey(User, related_name="owned_organizations", null=True)

    HEADLESS_ORG_NAME = "Unclaimed Networks"
    HEADLESS_ORG_PK = None  # keep the primary key of the headless org around, for efficiency
    HEADLESS_ORG_SAVE_FLAG = "internally_safe_headless_org_save"  # indicates safe save() call


    def add_zone(self, zone):
        return self.zones.add(zone)

    def get_zones(self):
        return self.zones.all().order_by("name")

    def add_member(self, user):
        return self.users.add(user)

    def get_members(self):
        return self.users.all()

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
        if self.name == Organization.HEADLESS_ORG_NAME:
            if kwargs.get(Organization.HEADLESS_ORG_SAVE_FLAG, False):
                del kwargs[Organization.HEADLESS_ORG_SAVE_FLAG]  # don't pass it on, it's an error
            elif self.pk != Organization.get_or_create_headless_organization().pk:
                raise Exception("Cannot save to reserved organization name: %s" % Organization.HEADLESS_ORG_NAME)

        super(Organization, self).save(*args, **kwargs)


    @classmethod
    def from_zone(cls, zone):
        """
        Given a zone, figure out which organizations contain it.
        """
        return Organization.objects.filter(zones=zone)


    @classmethod
    def get_or_create_headless_organization(cls, refresh_zones=False):
        """
        Retrieve the organization encapsulating all headless zones.
        """
        if cls.HEADLESS_ORG_PK is not None:
            # Already exists and cached, just query fast and return
            headless_org = cls.objects.get(pk=cls.HEADLESS_ORG_PK)

        else:
            # Potentially inefficient query, so limit this to once per server thread
            # by caching the results.  Here, we've had a cache miss
            headless_orgs = cls.objects.filter(name=cls.HEADLESS_ORG_NAME)
            if not headless_orgs:
                # Cache miss because the org actually doesn't exist.  Create it!
                headless_org = Organization(name=cls.HEADLESS_ORG_NAME)
                headless_org.save(**({cls.HEADLESS_ORG_SAVE_FLAG: True}))
                cls.HEADLESS_ORG_PK = headless_org.pk

            else:
                # Cache miss because it's the first relevant query since this thread started.
                assert len(headless_orgs) == 1, "Cannot have multiple HEADLESS ZONE organizations"
                cls.HEADLESS_ORG_PK = headless_orgs[0].pk
                headless_org = headless_orgs[0]

        # TODO(bcipolli): remove this code!
        #
        # In the future, when we self-register headless zones, we'll
        #    add them directly to the headless organization.
        #    For now, we'll have to do an exhaustive search.
        if refresh_zones:
            headless_org.zones.add(*Zone.get_headless_zones())

        return headless_org


class UserProfile(ExtendedModel):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return self.user.username

    def get_organizations(self):
        """
        Return all organizations that this user manages.

        If this user is a super-user, then the headless org will be appended at the end.
        """
        orgs = OrderedDict()  # no dictionary comprehensions, so have to loop
        for org in self.user.organization_set.all().order_by("name"):  # add in order queries (alphabetical?)
            orgs[org.pk] = org

        # Add a headless organization for superusers, containing
        #   any headless zones.
        # Make sure this is at the END of the list, so it is clearly special.
        if self.user.is_superuser:
            headless_org = Organization.get_or_create_headless_organization(refresh_zones=True)
            orgs[headless_org.pk] = headless_org

        return orgs


class OrganizationInvitation(ExtendedModel):
    email_to_invite = models.EmailField(verbose_name="Email of invitee", max_length=75)
    invited_by = models.ForeignKey(User)
    organization = models.ForeignKey(Organization, related_name="invitations")

    class Meta:
        unique_together = ('email_to_invite', 'organization')

    def save(self, *args, **kwargs):
        if self.invited_by and self.organization not in self.invited_by.organization_set.all():
            raise PermissionDenied("User %s does not have permissions to invite people on this organization." % self.invited_by)
        super(OrganizationInvitation, self).save(*args, **kwargs)

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


class DeletionRecord(ExtendedModel):
    organization = models.ForeignKey(Organization)
    deleter = models.ForeignKey(User, related_name="deletion_actor")
    deleted_user = models.ForeignKey(User, related_name="deletion_recipient", blank=True, null=True)
    deleted_invite = models.ForeignKey(OrganizationInvitation, blank=True, null=True)


class FeedListing(ExtendedModel):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    posted_date = models.DateTimeField()
    url = models.URLField()

    def get_absolute_url(self):
        return self.url

class Subscription(ExtendedModel):
    email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, blank=True)

