from annoying.functions import get_object_or_None
from django.contrib.auth.models import User, check_password
from django.core import serializers
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q
from django.utils.text import compress_string
from config.models import Settings
import crypto
import datetime
import uuid
import zlib
import settings
from pbkdf2 import crypt
from django.utils.translation import ugettext_lazy as _


_unhashable_fields = ["signature", "signed_by"]
_always_hash_fields = ["signed_version", "id"]

json_serializer = serializers.get_serializer("json")()

# ROOT_UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, settings.CENTRAL_SERVER_HOST)
ROOT_UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")


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
        return device.get_key().verify(self._hashable_representation(), signature)

    def verify_client_signature(self, signature):
        return self._verify_signature(self.client_device, signature)

    def verify_server_signature(self, signature):
        return self._verify_signature(self.server_device, signature)

    def sign(self):
        return Device.get_own_device().get_key().sign(self._hashable_representation())
        
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


class SyncedModelManager(models.Manager):
    
    def by_zone(self, zone):
        # get model instances that were signed by devices in the zone,
        # or signed by a trusted authority that said they were for the zone
        return self.filter(Q(signed_by__devicezone__zone=zone) |
            Q(signed_by__devicemetadata__is_trusted=True, zone_fallback=zone))

class SyncedModel(models.Model):
    id = models.CharField(primary_key=True, max_length=32, editable=False)
    counter = models.IntegerField()
    signature = models.CharField(max_length=360, blank=True, editable=False)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+")
    zone_fallback = models.ForeignKey("Zone", blank=True, null=True, related_name="+")
    deleted = models.BooleanField(default=False)

    objects = SyncedModelManager()

    def sign(self, device=None):
        if not self.id:
            self.id = self.get_uuid()
        self.signed_by = device or Device.get_own_device()
        self.signature = self.signed_by.get_key().sign(self._hashable_representation())

    def verify(self):
        # if nobody signed it, verification fails
        if not self.signed_by_id:
            return False
        # if it's not a trusted device...
        if not self.signed_by.get_metadata().is_trusted:
            # but it's a model class that requires trusted signatures, verification fails
            if self.requires_trusted_signature:
                return False
            if settings.CENTRAL_SERVER:
                # if it's not in a zone at all (or its DeviceZone was revoked), verification fails
                if not self.signed_by.get_zone():
                    return False
            else:
                # or if it's not in the same zone as our device (or the DeviceZone was revoked), verification fails
                if self.signed_by.get_zone() != Device.get_own_device().get_zone():
                    return False
        # by this point, we know that we're ok with accepting this model from the device that it says signed it
        # now, we just need to check whether or not it is actually signed by that model's private key
        try:
            return self.signed_by.get_key().verify(self._hashable_representation(), self.signature)
        except:
            return False
    
    def _hashable_fields(self, fields=None):
        
        # if no fields were specified, build a list of all the model's field names
        if not fields:
            fields = [field.name for field in self._meta.fields if field.name not in _unhashable_fields]
            # sort the list of fields, for consistency
            fields.sort()
        
        # certain fields should always be included
        for field in _always_hash_fields:
            if field not in fields:
                fields = [field] + fields
        
        # certain fields should never be included
        fields = [field for field in fields if field not in _unhashable_fields]
                
        return fields
    
    def _hashable_representation(self, fields=None):
        fields = self._hashable_fields(fields)
        chunks = []
        for field in fields:
            
            try:
                val = getattr(self, field)
            except ObjectDoesNotExist as e:
                # if it's a foreign key and is broken, just use the id of the related model
                val = getattr(self, field + "_id")
            
            if val:
                # convert models to just an id
                if isinstance(val, models.Model):
                    val = val.pk
                
                # convert datetimes to a str in a predictable way
                if isinstance(val, datetime.datetime):
                    val = ("%04d-%02d-%02d %d:%02d:%02d" %
                        (val.year, val.month, val.day, val.hour, val.minute, val.second))

                # encode string value as UTF-8, replacing any invalid characters so they don't blow up the hashing
                if isinstance(val, unicode):
                    val = val.encode("utf-8", "replace")

                # add this field/val pair onto the chunks to include in the hash
                chunks.append("%s=%s" % (field, val))
                
        return "&".join(chunks)

    def save(self, own_device=None, imported=False, increment_counters=True, *args, **kwargs):
        
        # we allow for the "own device" to be passed in so that a device can sign itself (before existing)
        own_device = own_device or Device.get_own_device()
        
        # this will probably never happen (since getting the device creates it), but just to be safe
        if not own_device:
            raise ValidationError("Cannot save any synced models before registering this Device.")
        
        # imported models are signed by other devices; make sure they check out
        if imported:
            if not self.signed_by_id:
                raise ValidationError("Imported models must be signed.")
            if not self.verify():
                raise ValidationError("Imported model's signature did not match.")
        else: # local models need to be signed by us
            self.counter = own_device.increment_and_get_counter()
            self.sign(device=own_device)
        
        # call the base Django Model save to write to the DB
        super(SyncedModel, self).save(*args, **kwargs)
        
        # for imported models, we want to keep track of the counter position we're at for that device
        if imported and increment_counters:
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
        # some models have a direct zone attribute; try for that
        zone = getattr(self, "zone", None)
        # otherwise, try getting the zone of the device that signed it
        if not zone and self.signed_by:
            zone = self.signed_by.get_zone()
        # otherwise, if it's signed by a trusted authority, try getting the fallback zone
        if not zone and self.signed_by and self.signed_by.get_metadata().is_trusted:
            zone = self.zone_fallback
        return zone
    get_zone.short_description = "Zone"

    def in_zone(self, zone):
        return zone == self.get_zone()

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

    def __unicode__(self):
        if not self.id:
            return self.name
        return "%s (#%s)" % (self.name, int(self.id[:3], 16))

    def is_default(self):
        return self.id == Settings.get("default_facility")


class FacilityGroup(SyncedModel):
    facility = models.ForeignKey(Facility, verbose_name=_("Facility"))
    name = models.CharField(max_length=30, verbose_name=_("Name"))
    
    def __unicode__(self):
        return self.name


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

    def __unicode__(self):
        return "%s (Facility: %s)" % (self.get_name(), self.facility)
        
    def check_password(self, raw_password):
        if self.password.split("$", 1)[0] == "sha1":
            # use Django's built-in password checker for SHA1-hashed passwords
            return check_password(raw_password, self.password)
        if self.password.split("$", 2)[1] == "p5k2":
            # use PBKDF2 password checking
            return self.password == crypt(raw_password, self.password)

    def set_password(self, raw_password):
        self.password = crypt(raw_password, iterations=Settings.get("password_hash_iterations", 2000))

    def get_name(self):
        if self.first_name and self.last_name:
            return u"%s %s" % (self.first_name, self.last_name)
        else:
            return self.username


class DeviceZone(SyncedModel):
    device = models.ForeignKey("Device", unique=True)
    zone = models.ForeignKey("Zone", db_index=True)
    revoked = models.BooleanField(default=False)
    max_counter = models.IntegerField(blank=True, null=True)
            
    requires_trusted_signature = True

    def __unicode__(self):
        return "Device: %s, assigned to Zone: %s" % (self.device, self.zone)


class SyncedLog(SyncedModel):
    category = models.CharField(max_length=50)
    value = models.CharField(max_length=250, blank=True)
    data = models.TextField(blank=True)


class DeviceManager(models.Manager):
    
    def by_zone(self, zone):
        # get Devices that belong to a particular zone, or are a trusted authority
        return self.filter(Q(devicezone__zone=zone, devicezone__revoked=False) |
            Q(devicemetadata__is_trusted=True))

class Device(SyncedModel):
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    public_key = models.CharField(max_length=500, db_index=True)

    objects = DeviceManager()
    
    key = None

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
        return uuid.uuid5(ROOT_UUID_NAMESPACE, str(self.public_key)).hex


settings.add_syncing_models([Facility, FacilityGroup, FacilityUser, SyncedLog])


class ImportPurgatory(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    counter = models.IntegerField()
    retry_attempts = models.IntegerField(default=0)
    model_count = models.IntegerField(default=0)
    serialized_models = models.TextField()
    exceptions = models.TextField()
    
    def save(self, *args, **kwargs):
        self.counter = self.counter or Device.get_own_device().get_counter()
        super(ImportPurgatory, self).save(*args, **kwargs)


def get_serialized_models(device_counters=None, limit=100, zone=None, include_count=False):
    
    # use the current device's zone if one was not specified
    if not zone:
        zone = Device.get_own_device().get_zone()
    
    # if no devices specified, assume we're starting from zero, and include all devices in the zone
    if device_counters is None:        
        device_counters = dict((device.id, 0) for device in Device.objects.by_zone(zone))
    
    # remove all requested devices that either don't exist or aren't in the correct zone
    for device_id in device_counters.keys():
        device = get_object_or_None(Device, pk=device_id)
        if not device or not (device.in_zone(zone) or device.get_metadata().is_trusted):
            del device_counters[device_id]
    
    models = []
    boost = 0
    
    # loop until we've found some models, or determined that there are none to get
    while True:
        
        # assume no instances remaining until proven otherwise
        instances_remaining = False
                
        # loop through all the model classes marked as syncable
        for Model in settings.syncing_models:
            
            # loop through each of the devices of interest
            for device_id, counter in device_counters.items():
                
                device = Device.objects.get(pk=device_id)
                queryset = Model.objects.filter(signed_by=device)
                
                # for trusted (central) device, only include models with the correct fallback zone
                if not device.in_zone(zone):
                    if device.get_metadata().is_trusted:
                        queryset = queryset.filter(zone_fallback=zone)
                    else:
                        continue

                # check whether there are any models that will be excluded by our limit, so we know to ask again
                if not instances_remaining and queryset.filter(counter__gt=counter+limit+boost).count() > 0:
                    instances_remaining = True
            
                # pull out the model instances within the given counter range
                models += queryset.filter(counter__gt=counter, counter__lte=counter+limit+boost)
                        
        # if we got some models, or there were none to get, then call it quits
        if len(models) > 0 or not instances_remaining:
            break

        # boost the effective limit, so we have a chance of catching something when we do another round
        boost += limit
    
    # serialize the models we found
    serialized_models = json_serializer.serialize(models, ensure_ascii=False)
        
    if include_count:
        return {"models": serialized_models, "count": len(models)}
    else:
        return serialized_models


def save_serialized_models(data, increment_counters=True):
    
    # if data is from a purgatory object, load it up
    if isinstance(data, ImportPurgatory):
        purgatory = data
        data = purgatory.serialized_models
    else:
        purgatory = None
    
    # deserialize the models, either from text or a list of dictionaries
    if isinstance(data, str) or isinstance(data, unicode):
        models = serializers.deserialize("json", data)
    else:
        models = serializers.deserialize("python", data)

    # try importing each of the models in turn
    unsaved_models = []
    exceptions = ""
    saved_model_count = 0
    for modelwrapper in models:
        try:
            
            # extract the model from the deserialization wrapper
            model = modelwrapper.object
            
            # only allow the importing of models that are subclasses of SyncedModel
            if not hasattr(model, "verify"):
                raise ValidationError("Cannot save model: %s does not have a verify method (not a subclass of SyncedModel?)" % model.__class__)
            
            # TODO(jamalex): more robust way to do this? (otherwise, it might barf about the id already existing)
            model._state.adding = False
            
            # verify that all fields are valid, and that foreign keys can be resolved
            model.full_clean()
            
            # save the imported model (checking that the signature is valid in the process)
            model.save(imported=True, increment_counters=increment_counters)
            
            # keep track of how many models have been successfully saved
            saved_model_count += 1
            
        except ValidationError as e: # the model could not be saved
            
            # keep a running list of models and exceptions, to be stored in purgatory
            exceptions += "%s: %s\n" % (model.pk, e)
            unsaved_models.append(model)
            
            # if the model is at least properly signed, try incrementing the counter for the signing device
            # (because otherwise we may never ask for additional models)
            try:
                if increment_counters and model.verify():
                    model.signed_by.set_counter_position(model.counter)
            except:
                pass
            
    # deal with any models that didn't validate properly; throw them into purgatory so we can try again later    
    if unsaved_models:
        if not purgatory:
            purgatory = ImportPurgatory()
        purgatory.serialized_models = json_serializer.serialize(unsaved_models, ensure_ascii=False)
        purgatory.exceptions = exceptions
        purgatory.model_count = len(unsaved_models)
        purgatory.retry_attempts += 1
        purgatory.save()
    elif purgatory: # everything saved properly this time, so we can eliminate the purgatory instance
        purgatory.delete()
    
    return {
        "unsaved_model_count": len(unsaved_models),
        "saved_model_count": saved_model_count,
    }

    
def get_device_counters(zone):
    device_counters = {}
    for device in Device.objects.by_zone(zone):
        if device.id not in device_counters:
            device_counters[device.id] = device.get_metadata().counter_position
    return device_counters
