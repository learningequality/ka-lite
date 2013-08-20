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
from securesync import crypto
from securesync.engine.models import SyncedModel


class RegisteredDevicePublicKey(models.Model):
    public_key = models.CharField(max_length=500, help_text="(This field will be filled in automatically)")
    zone = models.ForeignKey("Zone")

    class Meta:
        app_label = "securesync"

    def __unicode__(self):
        return u"%s... (Zone: %s)" % (self.public_key[0:5], self.zone)


class DeviceMetadata(models.Model):
    device = models.OneToOneField("Device", blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Device metadata"
        app_label = "securesync"

    def __unicode__(self):
        return u"(Device: %s)" % (self.device)


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    requires_trusted_signature = True

    class Meta:
        app_label = "securesync"

    #@central_server_only  # causes circular loop, to include here
    def get_org(self):
        """
        Reverse lookup of organization containing this zone.
        """
        orgs = self.organization_set.all()
        assert orgs.count() <= 1, "Zone must be contained by 0 or 1 organization(s)."

        return orgs[0] if orgs else None


    @classmethod
    def get_headless_zones(cls):
        """
        Method for getting all zones that aren't connected to at least one organization.
        """
        # Must import inline (not in header) to avoid import loop
        return Zone.objects.filter(organization=None)

    def __unicode__(self):
        return self.name


class DeviceZone(SyncedModel):
    device = models.ForeignKey("Device", unique=True)
    zone = models.ForeignKey("Zone", db_index=True)
    revoked = models.BooleanField(default=False)
    max_counter = models.IntegerField(blank=True, null=True)

    requires_trusted_signature = True

    class Meta:
        app_label = "securesync"

    def __unicode__(self):
        return u"Device: %s, assigned to Zone: %s" % (self.device, self.zone)


class DeviceManager(models.Manager):

    class Meta:
        app_label = "securesync"

    def by_zone(self, zone):
        # get Devices that belong to a particular zone, or are a trusted authority
        return self.filter(Q(devicezone__zone=zone, devicezone__revoked=False) |
            Q(devicemetadata__is_trusted=True))


class Device(SyncedModel):
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    public_key = models.CharField(max_length=500, db_index=True)
    version = models.CharField(max_length=len("10.10.100"), default="0.9.2", blank=True); version.minversion="0.9.3"  # default comes from knowing when this feature was implemented!

    objects = DeviceManager()
    key = None

    class Meta:
        app_label = "securesync"

    def set_key(self, key):
        self.public_key = key.get_public_key_string()
        self.key = key

    def get_key(self):
        if not self.key:
            if self.get_metadata().is_own_device:
                self.key = crypto.get_own_key()
            elif self.public_key:
                self.key = crypto.Key(public_key_string=self.public_key)
        return self.key

    def _hashable_representation(self):
        fields = ["signed_version", "name", "description", "public_key"]
        return super(Device, self)._hashable_representation(fields=fields)

    def get_metadata(self):
        try:
            return self.devicemetadata
        except DeviceMetadata.DoesNotExist:
            return DeviceMetadata(device=self)

    def set_counter_position(self, counter_position):
        metadata = self.get_metadata()
        if not metadata.device.id:
            return
        if counter_position > metadata.counter_position:
            metadata.counter_position = counter_position
            metadata.save()

    def full_clean(self):
        # TODO(jamalex): we skip out here, because otherwise self-signed devices will fail
        pass

    @classmethod
    def get_default_version(cls):
        """Accessor method to probe the default version of a device (or field)"""
        return cls._meta.get_field("version").default

    @staticmethod
    def get_own_device():
        devices = DeviceMetadata.objects.filter(is_own_device=True)
        if devices.count() == 0:
            own_device = Device.initialize_own_device(version=kalite.VERSION) # why don't we need name or description here?
        else:
            own_device = devices[0].device
        return own_device

    @staticmethod
    def initialize_own_device(**kwargs):
        own_device = Device(**kwargs)
        own_device.set_key(crypto.get_own_key())
        own_device.sign(device=own_device)
        own_device.save(own_device=own_device)
        metadata = own_device.get_metadata()
        metadata.is_own_device = True
        metadata.is_trusted = settings.CENTRAL_SERVER
        metadata.save()
        return own_device

    @transaction.commit_on_success
    def increment_and_get_counter(self):
        metadata = self.get_metadata()
        if not metadata.device.id:
            return 0
        metadata.counter_position += 1
        metadata.save()
        return metadata.counter_position

    def get_counter(self):
        metadata = self.get_metadata()
        if not metadata.device.id:
            return 0
        return metadata.counter_position

    def __unicode__(self):
        return self.name or self.id[0:5]

    def get_zone(self):
        zones = self.devicezone_set.filter(revoked=False)
        return zones and zones[0].zone or None
    get_zone.short_description = "Zone"

    def verify(self):
        if self.signed_by_id != self.id:
            return False
        return self.get_key().verify(self._hashable_representation(), self.signature)

    def save(self, is_trusted=False, *args, **kwargs):
        # TODO(jamalex): uncomment out the following, but allow for devices created on old versions somehow
        # if self.id and self.id != self.get_uuid():
        #     raise ValidationError("ID must match device's public key.")
        if self.signed_by_id and self.signed_by_id != self.id and not self.signed_by.get_metadata().is_trusted:
            raise ValidationError("Devices must either be self-signed or signed by a trusted authority.")
        super(Device, self).save(*args, **kwargs)
        if is_trusted:
            metadata = self.get_metadata()
            metadata.is_trusted = True
            metadata.save()

    def get_uuid(self):
        assert self.public_key is not None, "public_key required for get_uuid"

        return uuid.uuid5(settings.ROOT_UUID_NAMESPACE, str(self.public_key)).hex

    @staticmethod
    def get_device_counters(zone):
        device_counters = {}
        for device in Device.objects.by_zone(zone):
            if device.id not in device_counters:
                device_counters[device.id] = device.get_metadata().counter_position
        return device_counters


# No device data gets "synced" through the same sync mechanism as data--it is only synced 
#   through the special hand-shaking mechanism