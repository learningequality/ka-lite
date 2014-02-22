from django.db import models
from django.contrib.auth.models import User
import django_snippets.multiselect as multiselect

from utils.django_utils import ExtendedModel
from django.utils.translation import ugettext as _


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


class Contact(ExtendedModel):
    """Base contact information"""

    CONTACT_TYPES = ((CONTACT_TYPE_DEPLOYMENT, 'New Deployment'),
                     (CONTACT_TYPE_SUPPORT, 'Get Support'),
                     (CONTACT_TYPE_CONTRIBUTE,"Contribute"),
                     (CONTACT_TYPE_INFO, 'General Inquiries'))

    user      = models.ForeignKey(User, blank=True, null=True)  # user, but can be null (unregistered contact)
    name      = models.CharField(verbose_name=_("Your Name"), max_length=100)
    type      = models.CharField(max_length=12, choices=CONTACT_TYPES)
    email     = models.EmailField(verbose_name=_("Your Email"), max_length=100)
    org_name  = models.CharField(verbose_name=_("Organization Name"), max_length=100, blank=True)
    contact_date= models.DateField(auto_now_add=True)
    cc_email  = models.BooleanField(verbose_name=_("Please send a copy of this support request to the email address above."), default=False)
    ip        = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        return u"%s inquiry from %s @ %s on %s (%s)" % (self.type, self.name, self.org_name, self.contact_date, self.email)


class Deployment(ExtendedModel):
    """Deployment contact"""

    # The following values define limited options in the contact form
    DEPLOYMENT_INTERNET_ACCESS = (("none",_("The facilities have no internet access whatsoever.")),
                                  ("occasional", _("The facilities have occasional internet access, but it is rarely connected.")),
                                  ("slow", _("The facilities have very slow (e.g. 3G wireless or dialup) connections.")),
                                  ("expensive",_("Internet bandwidth is very expensive at these facilities.")),
                                  ("remote",_("There is internet access within reasonable transportation distance, so the server in this school can be taken and connected occasionally")),)
    DEPLOYMENT_HARDWARE = (("lan", _("The facilities have computer labs that have internal networks that student computers can connect to one another through.")),
                           ("server",_("The facilities have a central server that student computers can connect to.")),
                           ("no_network",_("The computers in these facilities cannot be networked.")),
                           ("none",_("The facilities do not currently have any infrastructure, and we will be supplying hardware.")),
                           ("roving",_("Servers will be in roving vans, visiting a number of facilities.")))

    # fields
    contact                 = models.ForeignKey(Contact)
    countries               = models.CharField(max_length=100, blank=True, verbose_name=_("What country/countries are you hoping to deploy in?"))
    internet_access         = multiselect.MultiSelectField(choices=DEPLOYMENT_INTERNET_ACCESS, max_length=100, blank=True, verbose_name=_("Which of the following statements accurately describe the internet access at your planned deployment?"))
    hardware_infrastructure = multiselect.MultiSelectField(choices=DEPLOYMENT_HARDWARE, max_length=100, blank=True, verbose_name=_("Which of the following statements accurately describe the hardware and infrastructure at your planned deployment?"))
    facilities              = models.TextField(blank=True, verbose_name=_("Please describe the facilities in more detail, to catch anything not covered above."),help_text=_("e.g. number of facilities, number of students at each, grade levels, languages spoken, etc."))
    low_cost_bundle         = models.TextField(blank=True, verbose_name=_("Would you be interested in the possibility of a low-cost (~$60), small, self-contained server solution, capable of running KA Lite?"))
    other                   = models.TextField(blank=True, verbose_name=_("Do you have any other questions or suggestions for us?"))

    def __unicode__(self):
        return u"Inquiry from %s @ %s on %s (%s)" % (self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Support(ExtendedModel):
    # Different support types (support contact sub-form)
    SUPPORT_TYPES = (('installation', 'Installation'),
                     ('setup',        'Post-install setup'),
                     ('downloading',  'Downloading videos'),
                     ('reporting',    'Coach reports'),
                     ('other',        'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=15, choices=SUPPORT_TYPES)
    issue    = models.TextField(blank=False, verbose_name="Please describe your issue.")

    def __unicode__(self):
        return u"%s inquiry from %s @ %s on %s (%s)" % (self.type, self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Contribute(ExtendedModel):
    """Want to contribute?  We have a form for that."""

    CONTRIBUTE_TYPES = ((CONTRIBUTE_TYPE_DEVELOPMENT, 'Code Development'),
                        (CONTRIBUTE_TYPE_FUNDING,     'Funding'),
                        (CONTRIBUTE_TYPE_TRANSLATION, 'Translation'),
                        (CONTRIBUTE_TYPE_TESTING,     'Testing'),
                        (CONTRIBUTE_TYPE_OTHER,       'Other'))

    contact  = models.ForeignKey(Contact)
    type     = models.CharField(max_length=15, choices=CONTRIBUTE_TYPES)
    issue    = models.TextField(blank=False, verbose_name="How would you like to contribute?")

    def __unicode__(self):
        return u"%s inquiry from %s @ %s on %s (%s)" % (self.type, self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)


class Info(ExtendedModel):
    contact  = models.ForeignKey(Contact)
    issue    = models.TextField(blank=False, verbose_name="What's on your mind?")
    
    def __unicode__(self):
        return u"Inquiry from %s @ %s on %s (%s)" % (self.contact.name, self.contact.org_name, self.contact.contact_date, self.contact.email)

