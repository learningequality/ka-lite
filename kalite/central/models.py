from django.db import models
from securesync.models import Zone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string

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

    def get_members(self):
        return list(self.users.all())

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
        return list(self.user.organization_set.all())

## Create new class of organization invites to check against people that have been invited

class OrganizationInvitation(models.Model):
    email_to_invite = models.EmailField(verbose_name="Email of invitee", max_length=75)
    invited_by = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)

    class Meta:
        unique_together = ('email_to_invite', 'organization')

    def send(self, request):
        to_email = self.email_to_invite
        sender = 'kalite@adhocsync.com'
        context = {
            'organization': self.organization,
            'invited_by': self.invited_by
        }
        if User.objects.filter(email=to_email).count() > 0:
            subject = render_to_string('org_invite_email_subject.txt', context)
            body = render_to_string('org_invite_email.txt', context)
        else:
            subject = render_to_string('central/central_invite_email_subject.txt', context)
            body = render_to_string('central/central_invite_email.txt', context)
        send_mail(subject, body, sender, [to_email], fail_silently=False)
