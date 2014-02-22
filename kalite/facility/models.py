from __future__ import absolute_import

import datetime
import uuid
import zlib
from annoying.functions import get_object_or_None
from pbkdf2 import crypt

from django.conf import settings
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
from securesync.engine.models import DeferredCountSyncedModel
from settings import LOG as logging
from utils.django_utils import verify_raw_password


class Facility(DeferredCountSyncedModel):
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
        app_label = "securesync"  # for back-compat reasons

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


class FacilityGroup(DeferredCountSyncedModel):
    facility = models.ForeignKey(Facility, verbose_name=_("Facility"))
    name = models.CharField(max_length=30, verbose_name=_("Name"))

    class Meta:
        app_label = "securesync"  # for back-compat reasons

    def __unicode__(self):
        return self.name


class FacilityUser(DeferredCountSyncedModel):
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
    default_language = models.CharField(max_length=8, blank=True, null=True); default_language.minversion="0.11.1"

    class Meta:
        unique_together = ("facility", "username")
        app_label = "securesync"  # for back-compat reasons

    def __unicode__(self):
        return u"%s (Facility: %s)" % (self.get_name(), self.facility)

    def save(self, *args, **kwargs):
        """
        Validate password format before saving
        """
        # Now, validate password.
        if self.password.split("$", 1)[0] == "sha1":
            # Django's built-in password checker for SHA1-hashed passwords
            pass

        elif len(self.password.split("$", 2)) == 3 and self.password.split("$", 2)[1] == "p5k2":
            # PBKDF2 password checking
            # Could fail if password doesn't split into parts nicely
            pass

        elif self.password:
            raise ValidationError(_("Unknown password format."))

        super(FacilityUser, self).save(*args, **kwargs)

        # in case the password was changed on another server, and then synced into here, clear cached password
        CachedPassword.invalidate_cached_password(user=self)

    def check_password(self, raw_password):
        cached_password = CachedPassword.get_cached_password(self)
        cur_password = cached_password or self.password

        # Check the password
        if cur_password.split("$", 1)[0] == "sha1":
            # use Django's built-in password checker for SHA1-hashed passwords
            okie_dokie = check_password(raw_password, cur_password)
        elif cur_password.split("$", 2)[1] == "p5k2":
            # use PBKDF2 password checking
            okie_dokie = cur_password == crypt(raw_password, cur_password)
        else:
            raise ValidationError(_("Unknown password format."))

        # Update on cached password-relevant stuff
        if okie_dokie and not cached_password and self.id:  # only can create if the user's been saved
            CachedPassword.set_cached_password(self, raw_password=raw_password)

        return okie_dokie

    def set_password(self, raw_password=None, hashed_password=None, cached_password=None):
        """Set a password with the raw password string, or the pre-hashed password.
        If using the raw string, """
        assert hashed_password is None or settings.DEBUG, "Only use hashed_password in debug mode."
        assert raw_password is not None or hashed_password is not None, "Must be passing in raw or hashed password"
        assert not (raw_password is not None and hashed_password is not None), "Must be specifying only one--not both."

        if raw_password:
            verify_raw_password(raw_password)

        if hashed_password:
            self.password = hashed_password

            # Can't save a cached password from a hash, so just make sure there is none.
            # Note: Need to do this, even if they're not enabled--we don't want to risk
            #   being out of sync (if people turn on/off/on the feature
            CachedPassword.invalidate_cached_password(user=self)

        else:
            n_iters = settings.PASSWORD_ITERATIONS_TEACHER_SYNCED if self.is_teacher else settings.PASSWORD_ITERATIONS_STUDENT_SYNCED
            self.password = crypt(raw_password, iterations=n_iters)

            if self.id:
                CachedPassword.set_cached_password(self, raw_password)

    def get_name(self):
        if self.first_name and self.last_name:
            return u"%s %s" % (self.first_name, self.last_name)
        else:
            return self.username


class CachedPassword(models.Model):
    """
    Local store of password hashes, using a locally settable # of password hash iterations.
    """
    user = models.ForeignKey("FacilityUser", unique=True)
    password = models.CharField(max_length=128)

    @classmethod
    def is_enabled(cls):
        # 0 is an illegal value, so 0 or None means disabled
        # Force both to be set; otherwise, assumptions below can break
        return bool(settings.PASSWORD_ITERATIONS_TEACHER and settings.PASSWORD_ITERATIONS_STUDENT)

    @classmethod
    def iters_for_user_type(cls, user):
        return settings.PASSWORD_ITERATIONS_TEACHER if user.is_teacher else settings.PASSWORD_ITERATIONS_STUDENT

    @classmethod
    def get_cached_password(cls, user):
        if not cls.is_enabled():
            return None

        # Cache miss because there is no row in the table for this user.
        cached_password = cls.is_enabled() and get_object_or_None(cls, user=user)
        if not cached_password:
            logging.debug("Cached password MISS (does not exist) for user=%s" % user.username)
            return None

        n_cached_iters = int(cached_password.password.split("$")[2], 16)  # this was determined
        if n_cached_iters == cls.iters_for_user_type(user):
            # Cache hit!
            logging.debug("Cached password hit for user=%s; cached iters=%d" % (user.username, n_cached_iters))
            return cached_password.password
        else:
            # Cache miss because the row is invalid (# hashes doesn't match the current cache setting)
            logging.debug("Cached password MISS (invalid) for user=%s" % user.username)
            cached_password.delete()
            return None

    @classmethod
    def invalidate_cached_password(cls, user):
        cls.objects.filter(user=user).delete()

    @classmethod
    def set_cached_password(cls, user, raw_password):
        assert user.id, "Your user must have an ID before calling this function."

        if not cls.is_enabled():
            # Must delete, to make sure we don't get out of sync.
            cls.invalidate_cached_password(user=user)

        else:
            try:
                # Set the cached password.
                n_cached_iters = cls.iters_for_user_type(user)
                # TODO(bcipolli) Migrate this to an extended django class
                #   that uses get_or_initialize
                cached_password = get_object_or_None(cls, user=user) or cls(user=user)
                cached_password.password = crypt(raw_password, iterations=n_cached_iters)
                cached_password.save()
                logging.debug("Set cached password for user=%s; iterations=%d" % (user.username, n_cached_iters))
            except Exception as e:
                # If we fail to create a cache item... just keep going--functionality
                #   can still move forward.
                logging.error(e)

    class Meta:
        app_label = "securesync"  # for back-compat reasons

engine.add_syncing_models([Facility, FacilityGroup, FacilityUser])
