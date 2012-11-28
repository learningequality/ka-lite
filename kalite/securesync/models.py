from django.contrib.auth.models import User, check_password
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db import models, transaction
from config.models import Settings
import crypto
import uuid
import random
import hashlib
import settings


_unhashable_fields = ["signature", "signed_by"]
_always_hash_fields = ["signed_version", "id"]

json_serializer = serializers.get_serializer("json")()

ROOT_UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, settings.CENTRAL_SERVER_HOST)


class SyncSession(models.Model):
    client_nonce = models.CharField(max_length=32, primary_key=True)
    client_device = models.ForeignKey("Device", related_name="client_sessions")
    server_nonce = models.CharField(max_length=32, blank=True)
    server_device = models.ForeignKey("Device", blank=True, null=True, related_name="server_sessions")
    verified = models.BooleanField(default=False)
    ip = models.CharField(max_length=50, blank=True)
    client_version = models.CharField(max_length=100, blank=True)
    client_os = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    models_uploaded = models.IntegerField(default=0)
    models_downloaded = models.IntegerField(default=0)
    closed = models.BooleanField(default=False)
    
    def _hashable_representation(self):
        return "%s:%s:%s:%s" % (
            self.client_nonce, self.client_device.pk,
            self.server_nonce, self.server_device.pk,
        )
        
    def _verify_signature(self, device, signature):
        return crypto.verify(self._hashable_representation(),
                             crypto.decode_base64(signature),
                             device.get_public_key())

    def verify_client_signature(self, signature):
        return self._verify_signature(self.client_device, signature)

    def verify_server_signature(self, signature):
        return self._verify_signature(self.server_device, signature)

    def sign(self):
        return crypto.encode_base64(crypto.sign(self._hashable_representation()))
        
    def __unicode__(self):
        return "%s... -> %s..." % (self.client_device.pk[0:5],
            (self.server_device and self.server_device.pk[0:5] or "?????"))


class RegisteredDevicePublicKey(models.Model):
    public_key = models.CharField(max_length=500, help_text="(this field should be filled in automatically; don't change it)")
    zone = models.ForeignKey("Zone")

    def __unicode__(self):
        return "%s... (Zone: %s)" % (self.public_key[0:5], self.zone)


class DeviceMetadata(models.Model):
    device = models.OneToOneField("Device", blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

    class Meta:    
        verbose_name_plural = "Device metadata"

    def __unicode__(self):
        return "(Device: %s)" % (self.device)


class SyncedModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    counter = models.IntegerField(editable=False)
    signature = models.CharField(max_length=360, blank=True, editable=False)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+", editable=False)

    def sign(self, device=None):
        self.signed_by = device or Device.get_own_device()
        self.signature = crypto.encode_base64(crypto.sign(self._hashable_representation()))

    def verify(self):
        if not self.signed_by_id:
            return False
        if self.requires_trusted_signature and not self.signed_by.get_metadata().is_trusted:
            return False
        key = self.signed_by.get_public_key()
        try:
            return crypto.verify(self._hashable_representation(), crypto.decode_base64(self.signature), key)
        except:
            return False
    
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

    def save(self, own_device=None, imported=False, *args, **kwargs):
        own_device = own_device or Device.get_own_device()
        if not own_device:
            raise ValidationError("Cannot save any synced models before registering this Device.")
        if imported:
            if not self.signed_by_id:
                raise ValidationError("Imported models must be signed.")
            if not self.verify():
                raise ValidationError("Imported model's signature did not match.")
        else: # local model
            if self.signed_by and self.signed_by != own_device:
                raise ValidationError("Cannot modify models signed by another device.")
            self.counter = own_device.increment_and_get_counter()
            if not self.id:
                self.id = self.get_uuid()
                super(SyncedModel, self).save(*args, **kwargs) # TODO(jamalex): can we get rid of this?
            self.sign(device=own_device)
        super(SyncedModel, self).save(*args, **kwargs)
        if imported:
            self.signed_by.set_counter_position(self.counter)

    def get_uuid(self):
        own_device = Device.get_own_device()
        namespace = own_device.id and uuid.UUID(own_device.id) or ROOT_UUID_NAMESPACE
        return uuid.uuid5(namespace, str(self.counter)).hex

    def get_existing_instance(self):
        uuid = self.id or self.get_uuid()
        try:
            return self.__class__.objects.get(id=uuid)
        except self.__class__.DoesNotExist:
            return None

    def get_zone(self):
        return getattr(self, "zone", None) or (self.signed_by and self.signed_by.get_zone()) or None

    requires_trusted_signature = False

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s... (Signed by: %s...)" % (self.pk[0:5], self.signed_by.pk[0:5])


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    requires_trusted_signature = True
    
    def __unicode__(self):
        return self.name
        

class Facility(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=400, blank=True)
    address_normalized = models.CharField(max_length=400, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    zoom = models.FloatField(blank=True, null=True)

    class Meta:    
        verbose_name_plural = "Facilities"

    def __unicode__(self):
        return "%s (#%s)" % (self.name, int(self.id[:3], 16))

    def is_default(self):
        return self.id == Settings.get("default_facility")


class FacilityGroup(SyncedModel):
    facility = models.ForeignKey(Facility)
    name = models.CharField(max_length=30)
    
    def __unicode__(self):
        return self.name


class FacilityUser(SyncedModel):
    facility = models.ForeignKey(Facility)
    group = models.ForeignKey(FacilityGroup, verbose_name="Group/class", blank=True, null=True, help_text="(optional)")
    username = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_teacher = models.BooleanField(default=False, help_text="(whether this user should have teacher permissions)")
    notes = models.TextField(blank=True)
    password = models.CharField(max_length=128, help_text="Use '[algo]$[salt]$[hexdigest]'.")

    class Meta:
        unique_together = ("facility", "username")

    def __unicode__(self):
        return "%s (Facility: %s)" % (self.get_name(), self.facility)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        hsh = hashlib.sha1(salt + raw_password).hexdigest()
        self.password = 'sha1$%s$%s' % (salt, hsh)

    def get_name(self):
        if self.first_name and self.last_name:
            return u"%s %s" % (self.first_name, self.last_name)
        else:
            return self.username


class DeviceZone(SyncedModel):
    device = models.ForeignKey("Device", unique=True)
    zone = models.ForeignKey("Zone", db_index=True)
            
    requires_trusted_signature = True

    def __unicode__(self):
        return "Device: %s, assigned to Zone: %s" % (self.device, self.zone)


class Device(SyncedModel):
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    public_key = models.CharField(max_length=500, db_index=True)

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

    def set_counter_position(self, counter_position):
        metadata = self.get_metadata()
        if not metadata.device.id:
            return
        if counter_position > metadata.counter_position:
            metadata.counter_position = counter_position
            metadata.save()

    @staticmethod
    def get_own_device():
        devices = DeviceMetadata.objects.filter(is_own_device=True)
        if devices.count() == 0:
            own_device = Device.initialize_own_device()
        else:
            own_device = devices[0].device
        return own_device
    
    @staticmethod
    def initialize_own_device(**kwargs):
        own_device = Device(**kwargs)
        own_device.set_public_key(crypto.get_public_key())
        own_device.sign(device=own_device)
        own_device.save(own_device=own_device)
        metadata = own_device.get_metadata()
        metadata.is_own_device = True
        metadata.is_trusted = True
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
        zones = self.devicezone_set.all()
        return zones.count() and zones[0].zone or None
    get_zone.short_description = "Zone"

    def verify(self):
        if self.signed_by_id != self.id:
            return False
        key = self.get_public_key()
        try:
            return crypto.verify(self._hashable_representation(), crypto.decode_base64(self.signature), key)
        except:
            return False

    def save(self, is_trusted=False, *args, **kwargs):
        super(Device, self).save(*args, **kwargs)
        if is_trusted:
            metadata = self.get_metadata()
            metadata.is_trusted = True
            metadata.save()

    def get_uuid(self):
        if not self.public_key:
            return uuid.uuid4()
        return uuid.uuid5(ROOT_UUID_NAMESPACE, str(self.public_key)).hex

settings.add_syncing_models([Facility, FacilityGroup, FacilityUser])

def get_serialized_models(device_counters=None, limit=100):
    if device_counters is None:
        device_counters = dict((device.id, 0) for device in Device.objects.all())
    models = []
    completed = False
    actual_limit = 0
    # loop until we've got something, or until there's nothing left
    while len(models) == 0 and not completed:
        # assume completed until proven otherwise
        completed = True
        # increase the actual limit by the limit size
        actual_limit += limit
        for Model in settings.syncing_models:
            for device_id, counter in device_counters.items():
                # check whether there are any models that will be excluded by our limit, so we know to ask again
                if Model.objects.filter(signed_by=device_id, counter__gte=counter+actual_limit).count() > 0:
                    completed = False
                models += Model.objects.filter(signed_by=device_id, counter__gte=counter, counter__lt=counter+actual_limit)
    return json_serializer.serialize(models, ensure_ascii=False, indent=2)
    
def save_serialized_models(data):
    if isinstance(data, str) or isinstance(data, unicode):
        models = serializers.deserialize("json", data)
    else:
        models = serializers.deserialize("python", data)
    unsaved_models = []
    saved_model_count = 0
    for model in models:
        try:
            # TODO(jamalex): more robust way to do this? (otherwise, it barfs about the id already existing):
            model.object._state.adding = False
            model.object.full_clean()
            # TODO(jamalex): also make sure that if the model already exists, it is signed by the same device
            # (to prevent devices from overwriting each other's models... or do we want to allow that?)
            model.object.save(imported=True)
            saved_model_count += 1
        except ValidationError as e:
            unsaved_models.append(model.object)
    return {
        "unsaved_model_count": len(unsaved_models),
        "saved_model_count": saved_model_count,
    }
    
def get_device_counters(zone):
    device_counters = {}
    for device_zone in DeviceZone.objects.filter(zone=zone):
        if device_zone.device.id not in device_counters:
            device_counters[device_zone.device.id] = device_zone.device.get_metadata().counter_position
    return device_counters
