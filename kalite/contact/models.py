from django.db import models
from django.contrib.auth.models import User

class Contact(models.Model):
    CONTACT_TYPE_DEPLOYMENT = 'deployment'
    CONTACT_TYPE_SUPPORT    = 'support'
    CONTACT_TYPE_INFO       = 'info'
    CONTACT_TYPES = ((CONTACT_TYPE_DEPLOYMENT, 'Deployment'),
                     (CONTACT_TYPE_SUPPORT, 'Support'),
                     (CONTACT_TYPE_INFO, 'General Inquiries'))
    user      = models.ForeignKey(User, blank=True, null=True)
    name      = models.CharField(verbose_name="Contact Name", max_length=100)
    type      = models.CharField(verbose_name="Reason for Contact", max_length=12, choices=CONTACT_TYPES)
    email     = models.EmailField(verbose_name="Contact Email", max_length=100)
    org_name  = models.CharField(verbose_name="Organization Name", max_length=100, blank=True)
    org_url   = models.URLField(verbose_name="Organization URL", blank=True)
    contact_date= models.DateField(auto_now_add=True)

    def __unicode__(self):
        return "%s inquiry from %s @ %s on %s (%s)"%(self.type, self.name, self.org_name, self.contact_date, self.email)
        
        
class Deployment(models.Model):
    contact                 = models.ForeignKey(Contact)
    countries               = models.CharField(max_length=100, blank=True)
    internet_access         = models.CharField(max_length=100, blank=True)
    hardware_infrastructure = models.TextField(blank=True)
    facilities              = models.TextField(blank=True)
    low_cost_bundle         = models.BooleanField(blank=True)
    other                   = models.TextField(blank=True)

    def __unicode__(self):
        return "Inquiry from %s @ %s on %s (%s)"%(self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Support(models.Model):
    SUPPORT_TYPES = (('installation', 'Installation'),
                     ('setup',        'Post-install setup'),
                     ('downloading',  'Downloading videos'),
                     ('reporting',    'Coach reports'),
                     ('other',        'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=5, choices=SUPPORT_TYPES)
    issue    = models.TextField(blank=True)

    def __unicode__(self):
        return "%s inquiry from %s @ %s on %s (%s)"%(self.type, self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Info(models.Model):
    contact  = models.ForeignKey(Contact)
    issue    = models.TextField(blank=True)
    
    def __unicode__(self):
        return "Inquiry from %s @ %s on %s (%s)"%(self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)

