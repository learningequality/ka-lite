from __future__ import absolute_import

import datetime
import uuid
import zlib
from annoying.functions import get_object_or_None
from pbkdf2 import crypt

from django.contrib.auth.models import check_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q
from django.utils.text import compress_string
from django.utils.translation import ugettext_lazy as _

import kalite
import settings
from config.models import Settings
from securesync import engine
from securesync.engine.models import SyncedModel


class Facility(SyncedModel):
    name = models.CharField(verbose_name=_("Name"), help_text=_("(This is the name that students/teachers will see when choosing their facility; it can be in the local language.)"), max_length=100)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    address = models.CharField(verbose_name=_("Address"), help_text=_("(Please provide as detailed an address as possible.)"), max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, verbose_name=_("Latitude"), null=True)
    longitude = models.FloatField(blank=True, verbose_name=_("Longitude"), null=True)
    zoom = models.FloatField(blank=True, verbose_name=_("Zoom"), null=True)
    contact_name = models.CharField(verbose_name=_("Contact Name"), help_text=_("(Who should we contact with any questions about this facility?)"), max_length=60, blank=True)
    contact_phone = models.CharField(max_length=60, verbose_name=_("Contact Phone"), blank=True)
    contact_email = models.EmailField(max_length=60, verbose_name=_("Contact Email"), blank=True)
    user_count = models.IntegerField(verbose_name=_("User Count"), help_text=_("(How many potential users do you estimate there are at this facility?)"), blank=True, null=True)

    class Meta:
        verbose_name_plural = "Facilities"
        app_label = "securesync"

    def __unicode__(self):
        if not self.id:
            return self.name
        return u"%s (#%s)" % (self.name, int(self.id[:3], 16))

    def is_default(self):
        return self.id == Settings.get("default_facility")


    @classmethod
    def from_zone(cls, zone):
        """Our best approximation of how to map facilities to zones"""

        facilities = set(Facility.objects.filter(zone_fallback=zone))

        for device_zone in DeviceZone.objects.filter(zone=zone):
            device = device_zone.device
            facilities = facilities.union(set(Facility.objects.filter(signed_by=device)))

        return facilities


class FacilityGroup(SyncedModel):
    facility = models.ForeignKey(Facility, verbose_name=_("Facility"))
    name = models.CharField(max_length=30, verbose_name=_("Name"))

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = "securesync"


class FacilityUser(SyncedModel):
    # Translators: This is a label in a form.
    facility = models.ForeignKey(Facility, verbose_name=_("Facility"))
    # Translators: This is a label in a form.
    group = models.ForeignKey(FacilityGroup, verbose_name=_("(Group/class)"), blank=True, null=True, help_text=_("(optional)"))
    # Translators: This is a label in a form.
    username = models.CharField(max_length=30, verbose_name=_("Username"))
    # Translators: This is a label in a form.
    first_name = models.CharField(max_length=30, verbose_name=_("First Name"), blank=True)
    # Translators: This is a label in a form.
    last_name = models.CharField(max_length=60, verbose_name=_("Last Name"), blank=True)
    # Translators: This is a label in a form.
    is_teacher = models.BooleanField(default=False, help_text=_("(whether this user should have teacher permissions)"))
    notes = models.TextField(blank=True)
    password = models.CharField(max_length=128)

    class Meta:
        unique_together = ("facility", "username")
        app_label = "securesync"

    def __unicode__(self):
        return u"%s (Facility: %s)" % (self.get_name(), self.facility)

    def check_password(self, raw_password):
        if self.password.split("$", 1)[0] == "sha1":
            # use Django's built-in password checker for SHA1-hashed passwords
            return check_password(raw_password, self.password)
        if self.password.split("$", 2)[1] == "p5k2":
            # use PBKDF2 password checking
            return self.password == crypt(raw_password, self.password)

    def set_password(self, raw_password=None, hashed_password=None):
        """Set a password with the raw password string, or the pre-hashed password."""

        assert hashed_password is None or settings.DEBUG, "Only use hashed_password in debug mode."
        assert raw_password is not None or hashed_password is not None, "Must be passing in raw or hashed password"
        assert not (raw_password is not None and hashed_password is not None), "Must be specifying only one--not both."

        if hashed_password:
            self.password = hashed_password
        else:
            self.password = crypt(raw_password, iterations=Settings.get("password_hash_iterations", 2000 if self.is_teacher else 1000))

    def get_name(self):
        if self.first_name and self.last_name:
            return u"%s %s" % (self.first_name, self.last_name)
        else:
            return self.username


engine.add_syncing_models([Facility, FacilityGroup, FacilityUser])
