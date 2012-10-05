from django.db import models, transaction
import crypto
import base64
import uuid


_unhashable_fields = ["signature", "signed_by"]
_always_hash_fields = ["signed_version", "id"]


class InvalidSignatureException(Exception):
    def __str__(self):
        return "The model's signature was invalid."


class DeviceSignerNotTrustedException(Exception):
    def __str__(self):
        return "The device is not signed by a trusted authority."


class OwnDeviceNotRegisteredException(Exception):
    def __str__(self):
        return "This device has not yet been registered."


class DeviceMetadata(models.Model):
    device = models.OneToOneField("Device")
    is_trusted_authority = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

class SyncedModel(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    counter = models.IntegerField()
    signature = models.CharField(max_length=90)
    signed_version = models.IntegerField(default=1)
    signed_by = models.ForeignKey("Device")

    def sign(self):
        self.signature = base64.encodestring(crypto.sign(self._hashable_representation(), key)).strip()

    def verify(self):
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
        
    def save(self, unsigned=False, *args, **kwargs):
        if not self.id:
            self.id = uuid.uuid1().hex
        if not unsigned:
            if not self.signature and not self.signed_by:
                own_device = Device.get_own_device()
                self.signed_by = own_device
                self.counter = own_device.increment_and_get_counter()
                self.sign()
            if not self.verify():
                raise InvalidSignatureException()
        super(SyncedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Organization(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)    


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    organization = models.ForeignKey("Organization")


class Facility(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    zone = models.ForeignKey(Zone)


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
        super(Device, self)._hashable_representation(fields=fields)

    def get_metadata(self):        
        try:
            return self.devicemetadata
        except DeviceMetadata.DoesNotExist:
            return DeviceMetadata(device=self)

    @staticmethod
    def get_own_device():
        devices = DeviceMetadata.objects.filter(is_own_device=True)
        if devices.count() == 0:
            raise OwnDeviceNotRegisteredException()
        return devices[0].device    
        
    def save(self):
        if not self.signed_by.get_metadata().is_trusted_authority():
            raise DeviceSignerNotTrustedException()
        super(Device, self).save()

    def save_as_trusted_authority(self):
        super(Device, self).save(unsigned=True)
        metadata = self.get_metadata()
        metadata.is_trusted_authority = True
        metadata.save()

    def save_as_own_device(self):
        super(Device, self).save()
        metadata = self.get_metadata()
        metadata.is_own_device = True
        metadata.save()

    @transaction.commit_on_success
    def increment_and_get_counter(self):
        metadata = self.get_metadata()
        metadata.counter_position += 1
        metadata.save()
        return metadata.counter_position

# Sync order:
#   Devices
