from django.core.exceptions import ValidationError
from django.db import models, transaction
import crypto
import base64
import uuid


_unhashable_fields = ["signature", "signed_by"]
_always_hash_fields = ["signed_version", "id"]


class DeviceMetadata(models.Model):
    device = models.OneToOneField("Device", blank=True, null=True)
    is_trusted_authority = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

class SyncedModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    counter = models.IntegerField()
    signature = models.CharField(max_length=90, blank=True)
    signed_version = models.IntegerField(default=1)
    signed_by = models.ForeignKey("Device", blank=True, null=True)

    def sign(self, device=None):
        self.signed_by = device or Device.get_own_device()
        self.signature = base64.encodestring(crypto.sign(self._hashable_representation())).strip()

    def verify(self):
        if not self.signed_by:
            return False
        key = self.signed_by.get_public_key()
        return crypto.verify(self._hashable_representation(), base64.decodestring(self.signature), key)
    
    def _hashable_representation(self, fields=None):
        if not fields:
            fields = [field.name for field in self._meta.fields if field not in _unhashable_fields]
            fields.sort()
        for field in _always_hash_fields:
            if field not in fields:
                fields = [field] + fields
        chunks = []
        for field in fields:
            val = getattr(self, field)
            if val:
                if isinstance(val, models.Model):
                    val = val.pk
                chunks.append("%s=%s" % (field, val))
        return "&".join(chunks)

    def save(self, own_device=None, *args, **kwargs):
        own_device = own_device or Device.get_own_device()
        namespace = own_device.id and uuid.UUID(own_device.id) or uuid.uuid4()
        if not self.counter:
            self.counter = own_device.increment_and_get_counter()
        if not self.id:
            self.id = uuid.uuid5(namespace, str(self.counter)).hex
        self.full_clean()
        super(SyncedModel, self).save()
        if not self.signature:
            self.sign(device=own_device)
        self.full_clean()
        super(SyncedModel, self).save(*args, **kwargs)

    def clean(self):
        if self.signature:
            if not self.verify():
                raise ValidationError("The model's signature was invalid.")
            if self.requires_authority_signature:
                if not self.signed_by.get_metadata().is_trusted_authority:
                    raise ValidationError("This model must be signed by a trusted authority.")

    class Meta:
        abstract = True

class Organization(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)    

    requires_authority_signature = True


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey("Organization")

    requires_authority_signature = True


class Facility(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    zone = models.ForeignKey(Zone)

    requires_authority_signature = True


class Device(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    primary_zone = models.ForeignKey(Zone, blank=True, null=True)
    public_key = models.CharField(max_length=200)

    def set_public_key(self, key):
        self.public_key = ":".join(base64.encodestring(x).strip() for x in key.pub())

    def get_public_key(self):
        return crypto.RSA.new_pub_key(base64.decodestring(q) for q in self.public_key.split(":"))

    def _hashable_representation(self):
        fields = ["signed_version", "name", "description", "primary_zone", "public_key"]
        return super(Device, self)._hashable_representation(fields=fields)

    def get_metadata(self):        
        try:
            return self.devicemetadata
        except DeviceMetadata.DoesNotExist:
            return DeviceMetadata(device=self)

    @staticmethod
    def get_own_device():
        devices = DeviceMetadata.objects.filter(is_own_device=True)
        if devices.count() == 0:
            return None
        return devices[0].device
            
    def save(self, self_signed=False, is_own_device=False, *args, **kwargs):
        super(Device, self).save(own_device=is_own_device and self or None, *args, **kwargs)
        if self_signed and is_own_device:
            self.set_public_key(crypto.public_key)
            self.sign(device=self)
            super(Device, self).save(own_device=self, *args, **kwargs)
        if self_signed:
            metadata = self.get_metadata()
            metadata.is_trusted_authority = True
            metadata.save()
        if is_own_device:
            metadata = self.get_metadata()
            metadata.is_own_device = True
            metadata.save()

    @transaction.commit_on_success
    def increment_and_get_counter(self):
        metadata = self.get_metadata()
        if not metadata.device.id:
            return 0
        metadata.counter_position += 1
        metadata.save()
        return metadata.counter_position
        
    requires_authority_signature = True

# Sync order:
#   Devices
