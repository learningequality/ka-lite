"""
Note: this module should not depend on central, 
so we can exclude shipping central server code
to distributed servers.
"""

import crypto
import datetime
import logging
import random
import uuid
import zlib
from annoying.functions import get_object_or_None
from pbkdf2 import crypt

from django.contrib.auth.models import User, check_password
from django.core import serializers
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q
from django.utils.text import compress_string
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

import kalite
import settings
import crypto
import model_sync
from config.utils import set_as_registered
from config.models import Settings



# Note: this MUST be hard-coded for backwards-compatibility reasons.
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
    errors = models.IntegerField(default=0); errors.version="0.9.4" # kalite version
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
    counter = models.IntegerField(default=0)
    signature = models.CharField(max_length=360, blank=True, editable=False)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+")
    zone_fallback = models.ForeignKey("Zone", blank=True, null=True, related_name="+")
    deleted = models.BooleanField(default=False)

    objects = SyncedModelManager()
    _unhashable_fields = ["signature", "signed_by"] # fields of this class to avoid serializing
    _always_hash_fields = ["signed_version", "id"]  # fields of this class to always serialize


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
            fields = [field.name for field in self._meta.fields if field.name not in self.__class__._unhashable_fields]
            # sort the list of fields, for consistency
            fields.sort()
        
        # certain fields should always be included
        for field in self.__class__._always_hash_fields:
            if field not in fields:
                fields = [field] + fields
        
        # certain fields should never be included
        fields = [field for field in fields if field not in self.__class__._unhashable_fields]
                
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
    
    def generate_install_certificates(self, num_certificates=5):
        
        certs = []
        if settings.CENTRAL_SERVER:
            for i in range(num_certificates):
                cert = self.zoneinstallcertificate_set.create()
                certs.append(cert)
                logging.debug("Created install certificate: Zone=%s; Cert=%s" % (self.name, cert.raw_value))
        return certs            
        
    @transaction.commit_on_success
    def register_offline(self, device, signed_values=None):
        """Registers in an offline context by verifying the given certificates
        with the zone's public key"""
        
        if device.is_registered():
            raise Exception("Device is already registered!")
        
        if signed_values:
            if hasattr(user_certificates,"pop"):
                user_certificates = [ZoneInstallCertificate.objects.get(signed_value=sv) for sv in signed_values]
            else:
                user_certificates = [ZoneInstallCertificate.objects.get(signed_value=signed_values)]
        else:
            user_certificates = ZoneInstallCertificate.objects.filter(zone=self.id)

        for cert in user_certificates:
            if cert.verify():
                # Things we have to do, in order to register
                dz = DeviceZone(device=device, zone=self)
                dz.save()
                set_as_registered()

                # Things we'd like to do, in order to facilitate user registrations:
                #    Create a default facility.
                if len(Facility.objects.all())==0:
                    facility = Facility(name="default facility")
                    facility.save()

                return cert.raw_value
        return None
        
    def __unicode__(self):
        return self.name


class ZoneKey(SyncedModel):
    """Zones should have keys, but for back compat, they can't.
    So, let's define a one-to-one table, to store zone keys.
    
    ZoneKey gets created on the fly, whenever something happens
    that requires one.  Note that right now, that is when
    a ZoneInstallCertificate is requested."""
    
    zone = models.ForeignKey(Zone, verbose_name="Zone", unique=True)
    private_key = models.TextField(max_length=500, blank=True) # distributed server
    public_key = models.TextField(max_length=500)
    
    key = None
    
    def save(self, *args, **kwargs):
        # This happens on the local server side
        if self.public_key:
            assert self.private_key or not settings.CENTRAL_SERVER, "public_key should only be set alone in distributed servers."
            
        # Auto-generate keys, if necessary
        elif not self.private_key:
            key = crypto.Key()
            self.private_key = key.get_private_key_string()
            self.public_key  = key.get_public_key_string()
            
        else:# self.public_key:
            self.public_key = self.get_key().get_public_key_string()
        
        super(ZoneKey, self).save(*args, **kwargs)
        
        
    def get_key(self):

        # We have a cryptographic key object (from previous run); return it
        if self.key:
            return self.key

        # We have key strings, but no key object.  create one!
        elif self.private_key:
            # For back-compatibility, where zones didn't have keys
            if self.private_key=="dummy_key":
                self.private_key = None
                self.public_key = None
                self.save()
                
            self.key = crypto.Key(private_key_string = self.private_key, public_key_string = self.public_key)
            return self.key

        elif self.public_key:
            self.key = crypto.Key(public_key_string = self.public_key)
            return self.key
            
        else:  
            # Cannot create a key here; otherwise we run the risk
            #   of changing the key (if it's generated here and not saved)
            raise Exception('No key set for this object.')

        
class ZoneInstallCertificate(models.Model):
    """Install certificates are used to validate the addition of a 
    device to a zone during an offline install, with some guarantee
    that if the device ever comes online, the central server will approve the addition.
    """
    
    zone = models.ForeignKey(Zone, verbose_name="Zone Certificate")
    raw_value = models.CharField(max_length=50, blank=False)
    signed_value = models.CharField(max_length=500, blank=False)
    expiration_date = models.DateTimeField()
    
    
    @transaction.commit_on_success
    def save(self, *args, **kwargs):

        # Generate the certificate
        if not self.raw_value:
            self.raw_value = "%f" % random.random()
            self.signed_value = ""
        
        if not self.signed_value:
            self.signed_value = self.get_key().sign(self.raw_value)
        
        # Make sure we don't get duplicate certificates
        cert_ids = set([cert.id for cert in ZoneInstallCertificate.objects.filter(zone=self.id,  raw_value=self.raw_value)]).union(set((self.id,)))
        if len(cert_ids) != 1:
            raise Exception("Cannot double-add install certificates.")
        
        # Expire in one year, if not specified
        #   Note: no "years" nor "month" keywords, so set in days
        if not self.expiration_date:
            self.expiration_date = datetime.datetime.now() + datetime.timedelta(days=365) 
            
        super(ZoneInstallCertificate, self).save(*args, **kwargs)


    def get_key(self):
        if not getattr(self, "zonekey", None):
            try:
                self.zonekey = ZoneKey.objects.get(zone=self.zone)
            except ZoneKey.DoesNotExist:
                # generate the zone key
                self.zonekey = ZoneKey(zone=self.zone)
                self.zonekey.save()
                self.zonekey.full_clean()
        return self.zonekey.get_key()
    
    
    def verify(self):
        """Check that the given certificate is recognized, but don't actually use it."""
        
        return self.get_key().verify(self.raw_value, self.signed_value)
            
                
    def use(self):
        """Use the given install certificate: validate it, and remove it from the database.
        If the certificate was invalid/unrecognized, then the method with raise an Exception"""
        
        self.delete()


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
    version = models.CharField(max_length=len("10.10.100"), default="0.9.2", blank=True); version.version="0.9.4" # default comes from knowing when this feature was implemented!

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

    def is_registered(self):
        return self.get_zone() is not None
        
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
        """Device sets own counter (in metadata), and returns it (for update)"""
        
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

    @staticmethod    
    def get_device_counters(zone):
        device_counters = {}
        for device in Device.objects.by_zone(zone):
            if device.id not in device_counters:
                device_counters[device.id] = device.get_metadata().counter_position
        return device_counters
    
    
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


model_sync.add_syncing_models([Facility, FacilityGroup, FacilityUser, SyncedLog])
