from django.contrib.auth.models import User, get_hexdigest, check_password
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models, transaction
import crypto
import base64
import uuid


_unhashable_fields = ["signature", "signed_by"]
_always_hash_fields = ["signed_version", "id"]

json_serializer = serializers.get_serializer("json")()


class SyncSession(models.Model):
    client_nonce = models.CharField(max_length=32, primary_key=True)
    client_device = models.ForeignKey("Device", related_name="client_sessions")
    server_nonce = models.CharField(max_length=32, blank=True)
    server_device = models.ForeignKey("Device", blank=True, null=True, related_name="server_sessions")
    verified = models.BooleanField(default=False)
    
    def _hashable_representation(self):
        return "%s:%s:%s:%s" % (
            self.client_nonce, self.client_device.pk,
            self.server_nonce, self.server_device.pk,
        )
        
    def _verify_signature(self, device, signature):
        return crypto.verify(self._hashable_representation(),
                             base64.decodestring(signature),
                             device.get_public_key())

    def verify_client_signature(self, signature):
        return self._verify_signature(self.client_device, signature)

    def verify_server_signature(self, signature):
        return self._verify_signature(self.server_device, signature)

    def sign(self):
        return base64.encodestring(crypto.sign(self._hashable_representation())).strip()
        
    def __unicode__(self):
        return "%s... -> %s..." % (self.client_device.pk[0:5], self.server_device.pk[0:5])


class RegisteredDevicePublicKey(models.Model):
    public_key = models.CharField(max_length=200, primary_key=True)
    zone = models.ForeignKey("Zone")

    def __unicode__(self):
        return "%s... (Zone: %s)" % (self.public_key[0:5], self.zone)


class DeviceMetadata(models.Model):
    device = models.OneToOneField("Device", blank=True, null=True)
    is_trusted_authority = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

    class Meta:    
        verbose_name_plural = "Device metadata"

    def __unicode__(self):
        return "(Device: %s)" % (self.device)


class SyncedModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    counter = models.IntegerField(editable=False)
    signature = models.CharField(max_length=90, blank=True, editable=False)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+", editable=False)

    def sign(self, device=None):
        self.signed_by = device or Device.get_own_device()
        self.signature = base64.encodestring(crypto.sign(self._hashable_representation())).strip()

    def verify(self):
        if not self.signed_by:
            return False
        if self.requires_authority_signature and not self.signed_by.get_metadata().is_trusted_authority:
            return False
        key = self.signed_by.get_public_key()
        return crypto.verify(self._hashable_representation(), base64.decodestring(self.signature), key)
    
    def _hashable_representation(self, fields=None):
        if not fields:
            fields = [field.name for field in self._meta.fields if field.name not in _unhashable_fields]
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
        if not own_device:
            raise ValidationError("Cannot save any synced models before registering this Device.")
        self.counter = own_device.increment_and_get_counter()
        if not self.id:
            namespace = own_device.id and uuid.UUID(own_device.id) or uuid.uuid4()
            self.id = uuid.uuid5(namespace, str(self.counter)).hex
            super(SyncedModel, self).save(*args, **kwargs) # TODO(jamalex): can we get rid of this?
        if not self.signed_by or self.signed_by == own_device:
            self.sign(device=own_device)
        super(SyncedModel, self).save(*args, **kwargs)

    requires_authority_signature = False

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s... (Signed by: %s...)" % (self.pk[0:5], self.signed_by.pk[0:5])



class Organization(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    url = models.URLField(verbose_name="Website URL", blank=True)

    requires_authority_signature = True
    
    def get_zones(self):
        return Zone.objects.filter(pk__in=[zo.zone.pk for zo in self.zoneorganization_set.all()])

    def __unicode__(self):
        return self.name


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    requires_authority_signature = True
    
    def __unicode__(self):
        return self.name


ZONE_ORG_ROLES = (
    ("superuser", "Full administrative privileges"),
    ("analytics", "Can view analytics, but not administer")
)

class ZoneOrganization(SyncedModel):
    zone = models.ForeignKey(Zone)
    organization = models.ForeignKey(Organization)
    role = models.CharField(max_length=15, choices=ZONE_ORG_ROLES)
    notes = models.TextField(blank=True)

    requires_authority_signature = True
    
    def __unicode__(self):
        return "Zone: %s, Organization: %s" % (self.zone, self.organization)
        

class OrganizationUser(models.Model):
    user = models.ForeignKey(User)
    organization = models.ForeignKey(Organization)

    def get_zones(self):
        return self.organization.get_zones()

    def __unicode__(self):
        return "%s (Organization: %s)" % (self.user, self.organization)


class Facility(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    zone = models.ForeignKey(Zone)

    requires_authority_signature = True

    class Meta:    
        verbose_name_plural = "Facilities"

    def __unicode__(self):
        return "%s (Zone: %s)" % (self.name, self.zone)


class FacilityUser(SyncedModel):
    facility = models.ForeignKey(Facility)
    username = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    password = models.CharField(max_length=128, help_text="Use '[algo]$[salt]$[hexdigest]'.")

    class Meta:
        unique_together = ("facility", "username")

    def __unicode__(self):
        return "%s (Facility: %s)" % ((self.first_name + " " + self.last_name).strip() or self.username, self.facility)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        import random
        algo = 'sha1'
        salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
        hsh = get_hexdigest(algo, salt, raw_password)
        self.password = '%s$%s$%s' % (algo, salt, hsh)


class DeviceZone(SyncedModel):
    device = models.ForeignKey("Device")
    zone = models.ForeignKey("Zone")
    primary = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ("device", "zone")
        
    requires_authority_signature = True

    def __unicode__(self):
        return "Device: %s, Zone: %s" % (self.device, self.zone)


class Device(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    public_key = models.CharField(max_length=200)
    revoked = models.BooleanField(default=False)

    def set_public_key(self, key):
        self.public_key = crypto.serialize_public_key(key)

    def get_public_key(self):
        return crypto.deserialize_public_key(self.public_key)

    def _hashable_representation(self):
        fields = ["signed_version", "name", "description", "public_key"]
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
    
    @staticmethod
    def initialize_central_authority_device(name):
        own_device = Device()
        own_device.name = name
        own_device.set_public_key(crypto.public_key)
        own_device.save(self_signed=True, is_own_device=True)
            
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
        
    def __unicode__(self):
        return self.name
        
    requires_authority_signature = True

syncing_models = [Device, Organization, Zone, DeviceZone, ZoneOrganization, Facility, FacilityUser]

def get_serialized_models(device_counters=None, limit=1000):
    if not device_counters:
        device_counters = dict((device.id, 0) for device in Device.objects.all())
    models = []
    for Model in syncing_models:
        for device_id, counter in device_counters.items():
            models += Model.objects.filter(signed_by=device_id, counter__gte=counter)
            if len(models) > limit:
                return json_serializer.serialize(models[0:limit], ensure_ascii=False, indent=2)
    return json_serializer.serialize(models, ensure_ascii=False, indent=2)
    
def save_serialized_models(data):
    models = serializers.deserialize("json", data)
    unsaved_models = []
    for model in models:
        try:
            # TODO(jamalex): more robust way to do this? (otherwise, it barfs about the id already existing):
            model.object._state.adding = False
            model.object.full_clean()
            if not model.verify():
                raise ValidationError("The signature did not match!")
            model.save()
        except ValidationError as e:
            print "Error saving model %s: %s" % (model, e)
            unsaved_models.append(model.object)
    return unsaved_models
    
