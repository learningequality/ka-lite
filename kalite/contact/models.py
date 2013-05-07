from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    CONTACT_TYPE_DEPLOYMENT = 'depl'
    CONTACT_TYPE_SUPPORT    = 'supp'
    CONTACT_TYPE_INFO       = 'info'
    CONTACT_TYPES = ((CONTACT_TYPE_DEPLOYMENT, 'Deployment'),
                     (CONTACT_TYPE_SUPPORT, 'Support'),
                     (CONTACT_TYPE_INFO, 'General Inquiries'))
    user      = models.ForeignKey(User, blank=True)
    name      = models.CharField(verbose_name="Contact name", max_length=100)
    type      = models.CharField(verbose_name="Contact type", max_length=4, choices=CONTACT_TYPES)
    email     = models.EmailField(verbose_name="Contact email", max_length=100)
    org_name  = models.CharField(verbose_name="Organization name", max_length=100, blank=True)
    org_url   = models.URLField(verbose_name="Organziation_url URL", help_text="<br/>(optional)", blank=True)

class Deployment(models.Model):
    contact                 = models.ForeignKey(Contact)
    countries               = models.CharField(max_length=100, blank=True)
    internet_access         = models.CharField(max_length=100, blank=True)
    hardware_infrastructure = models.TextField(blank=True)
    facilities              = models.TextField(blank=True)
    low_cost_bundle         = models.BooleanField(blank=True)
    other                   = models.TextField(blank=True)

class Support(models.Model):
    SUPPORT_TYPES = (('instl', 'Installation'),
                     ('setup', 'Post-install setup'),
                     ('dwnld', 'Downloading videos'),
                     ('corpt', 'Coach reports'),
                     ('other', 'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=5, choices=SUPPORT_TYPES)
    issue    = models.TextField(blank=True)

class Info(models.Model):
    contact  = models.ForeignKey(Contact)
    issue    = models.TextField(blank=True)

