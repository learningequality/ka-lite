from django.db import models
from django.contrib.auth.models import User
import django_snippets.multiselect as multiselect


# Different contact types
CONTACT_TYPE_DEPLOYMENT = 'deployment'
CONTACT_TYPE_SUPPORT    = 'support'
CONTACT_TYPE_CONTRIBUTE = 'contribute'
CONTACT_TYPE_INFO       = 'info'

# Contribute types (contribute contact sub-form)
CONTRIBUTE_TYPE_DEVELOPMENT='development'
CONTRIBUTE_TYPE_FUNDING    ='funding'
CONTRIBUTE_TYPE_TRANSLATION='translation'
CONTRIBUTE_TYPE_TESTING    ='testing'
CONTRIBUTE_TYPE_OTHER      ='other'


class Contact(models.Model):
    """Base contact information"""

    CONTACT_TYPES = ((CONTACT_TYPE_DEPLOYMENT, 'New Deployment'),
                     (CONTACT_TYPE_SUPPORT, 'Support'),
                     (CONTACT_TYPE_CONTRIBUTE,"Contribute"),
                     (CONTACT_TYPE_INFO, 'General Inquiries'))

    user      = models.ForeignKey(User, blank=True, null=True)  # user, but can be null (unregistered contact)
    name      = models.CharField(verbose_name="Your Name", max_length=100)
    type      = models.CharField(verbose_name="Reason for Contact", max_length=12, choices=CONTACT_TYPES)
    email     = models.EmailField(verbose_name="Your Email", max_length=100)
    org_name  = models.CharField(verbose_name="Organization Name", max_length=100, blank=True)
    org_url   = models.URLField(verbose_name="Organization URL", blank=True)
    contact_date= models.DateField(auto_now_add=True)
    cc_email  = models.BooleanField(verbose_name="Please send a copy of this support request to the email address above.", default=False)

    def __unicode__(self):
        return "%s inquiry from %s @ %s on %s (%s)"%(self.type, self.name, self.org_name, self.contact_date, self.email)


class Deployment(models.Model):
    """Deployment contact"""

    # The following values define limited options in the contact form
    DEPLOYMENT_INTERNET_ACCESS = (("none","The facilities have no internet access whatsoever."),
                                  ("occasional", "The facilities have occasional internet access, but it is rarely connected."),
                                  ("slow", "The facilities have very slow (e.g. 3G wireless or dialup) connections."),
                                  ("expensive","Internet bandwidth is very expensive at these facilities."),
                                  ("remote","There is internet access within reasonable transportation distance, so the server in this school can be taken and connected occasionally"),)
    DEPLOYMENT_HARDWARE = (("lan", "The facilities have computer labs that have internal networks that student computers can connect to one another through."),
                           ("server","The facilities have a central server that student computers can connect to."),
                           ("no_network","The computers in these facilities cannot be networked."),
                           ("none","The facilities do not currently have any infrastructure, and we will be supplying hardware."),
                           ("roving","Servers will be in roving vans, visiting a number of facilities."))

    # fields
    contact                 = models.ForeignKey(Contact)
    countries               = models.CharField(max_length=100, blank=True, verbose_name="What country/countries are you hoping to deploy in?")
    internet_access         = multiselect.MultiSelectField(choices=DEPLOYMENT_INTERNET_ACCESS, max_length=100, blank=True, verbose_name="Which of the following statements accurately describe the internet access at your planned deployment?")
    hardware_infrastructure = multiselect.MultiSelectField(choices=DEPLOYMENT_HARDWARE, max_length=100, blank=True, verbose_name="Which of the following statements accurately describe the hardware and infrastructure at your planned deployment?")
    facilities              = models.TextField(blank=True,verbose_name="Please describe the facilities in more detail, to catch anything not covered above.",help_text="e.g. number of facilities, number of students at each, grade levels, languages spoken, etc.")
    low_cost_bundle         = models.TextField(blank=True,verbose_name="Would you be interested in the possibility of a low-cost (~$60), small, self-contained server solution, capable of running KA Lite?")
    other                   = models.TextField(blank=True,verbose_name="Do you have any other questions or suggestions for us?")

    def __unicode__(self):
        return "Inquiry from %s @ %s on %s (%s)"%(self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Support(models.Model):
    # Different support types (support contact sub-form)
    SUPPORT_TYPES = (('installation', 'Installation'),
                     ('setup',        'Post-install setup'),
                     ('downloading',  'Downloading videos'),
                     ('reporting',    'Coach reports'),
                     ('other',        'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=15, choices=SUPPORT_TYPES, verbose_name="Issue Type")
    issue    = models.TextField(blank=True, verbose_name="Please describe your issue.")

    def __unicode__(self):
        return "%s inquiry from %s @ %s on %s (%s)"%(self.type, self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Contribute(models.Model):
    """Want to contribute?  We have a form for that."""

    CONTRIBUTE_TYPES = ((CONTRIBUTE_TYPE_DEVELOPMENT, 'Code Development'),
                        (CONTRIBUTE_TYPE_FUNDING,     'Funding'),
                        (CONTRIBUTE_TYPE_TRANSLATION, 'Translation'),
                        (CONTRIBUTE_TYPE_TESTING,     'Testing'),
                        (CONTRIBUTE_TYPE_OTHER,       'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=15, choices=CONTRIBUTE_TYPES, verbose_name="Type of contribution:")
    issue    = models.TextField(blank=True, verbose_name="How would you like to contribute?")

    def __unicode__(self):
        return "%s inquiry from %s @ %s on %s (%s)"%(self.type, self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Info(models.Model):
    contact  = models.ForeignKey(Contact)
    issue    = models.TextField(blank=True, verbose_name="What's on your mind?")
    
    def __unicode__(self):
        return "Inquiry from %s @ %s on %s (%s)"%(self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)

