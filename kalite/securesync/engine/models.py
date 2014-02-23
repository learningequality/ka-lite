import datetime
import uuid
import zlib
from pbkdf2 import crypt

from django.contrib.auth.models import check_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from django.utils.text import compress_string
from django.utils.translation import ugettext_lazy as _

import kalite
import settings
from . import add_syncing_models
from config.models import Settings
from settings import LOG as logging
from utils.django_utils import validate_via_booleans, ExtendedModel


ID_MAX_LENGTH=32
IP_MAX_LENGTH=50

def _get_own_device():
    """
    To allow imports to resolve... the only ugly thing of this code separation.
    """
    from securesync.devices.models import Device
    return Device.get_own_device()


class SyncSession(ExtendedModel):
    client_nonce = models.CharField(max_length=ID_MAX_LENGTH, primary_key=True)
    client_device = models.ForeignKey("Device", related_name="client_sessions")
    server_nonce = models.CharField(max_length=ID_MAX_LENGTH, blank=True)
    server_device = models.ForeignKey("Device", blank=True, null=True, related_name="server_sessions")
    verified = models.BooleanField(default=False)
    ip = models.CharField(max_length=IP_MAX_LENGTH, blank=True)
    client_version = models.CharField(max_length=100, blank=True)
    client_os = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    models_uploaded = models.IntegerField(default=0)
    models_downloaded = models.IntegerField(default=0)
    errors = models.IntegerField(default=0); errors.minversion="0.9.3" # kalite version
    closed = models.BooleanField(default=False)

    class Meta:
        app_label = "securesync"

    def __unicode__(self):
        return u"%s... -> %s..." % (self.client_device.pk[0:5],
            (self.server_device and self.server_device.pk[0:5] or "?????"))

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
        return _get_own_device().get_key().sign(self._hashable_representation())

    def save(self, *args, **kwargs):
        """
        Save, while obeying the max count.
        """
        super(SyncSession,self).save(*args, **kwargs)
        # TODO(bcipolli): think about adding an index for efficiency
        #   to timestamp, making sure that whatever we do works for both
        #   distributed and central servers.
        if settings.SYNC_SESSIONS_MAX_RECORDS is not None and SyncSession.objects.count() > settings.SYNC_SESSIONS_MAX_RECORDS:
            to_discard = SyncSession.objects.order_by("timestamp")[0:SyncSession.objects.count()-settings.SYNC_SESSIONS_MAX_RECORDS]
            SyncSession.objects.filter(pk__in=to_discard).delete()


class SyncedModelManager(models.Manager):

    class Meta:
        app_label = "securesync"

    def by_zone(self, zone):
        """Get model instances that were signed by devices in the zone,
        or signed by a trusted authority that said they were for the zone,
        or not signed at all and we're looking for models in our own zone.
        """

        condition = \
            Q(signed_by__devicezone__zone=zone, signed_by__devicezone__revoked=False) | \
            Q(signed_by__devicemetadata__is_trusted=True, zone_fallback=zone)

        # Due to deferred signing, we need to consider completely unsigned models to be in our own zone.
        if zone == _get_own_device().get_zone():
            condition = condition | Q(signed_by=None)

        return self.filter(condition)


class SyncedModel(ExtendedModel):
    """
    The main class that makes this engine go.

    A model that is cross-computer syncable.  All models sync'd across computers
    should inherit from this base class.

    NOTE on signed_version (bcipolli; 2013/10/10):
    signed_version is part of a design where schema changes forced models into ImportPurgatory,
    where they would stay until a software upgrade.

    Due to the deployment (and worldwide use) of code with a bug in the implementation of that design,
    a second design was implemented and deployed.  There, unknown models and model fields (judged by
    comparing the model/field's "minversion" property with the remote server's version) are
    simply not shared over the wire.  This system only works for distributed-central interactions,
    and interactions between peers of the same (schema) version, and will not work for any
    mixed version P2P syncing.

    For backwards compatibility reasons, signed_version must remain, and would be used
    in future designs/implementations reusing the original (elegant) design that is appropriate
    for mixed version P2P sync.
    """
    id = models.CharField(primary_key=True, max_length=ID_MAX_LENGTH, editable=False)
    counter = models.IntegerField(default=None, blank=True, null=True)
    signature = models.CharField(max_length=360, blank=True, editable=False, null=True)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+")
    zone_fallback = models.ForeignKey("Zone", blank=True, null=True, related_name="+")
    deleted = models.BooleanField(default=False)

    objects = SyncedModelManager()
    _unhashable_fields = ["signature", "signed_by"] # fields of this class to avoid serializing
    _always_hash_fields = ["signed_version", "id"]  # fields of this class to always serialize (see note above for signed_version)

    class Meta:
        abstract = True
        app_label = "securesync"

    def sign(self, device=None):
        """
        Get all of the relevant fields of this model into a single string (self._hashable_representation()),
        then sign it with the specified device (if specified), or the current device.
        """
        device = device or _get_own_device()
        assert device.get_key(), "Cannot sign with device %s: key does not exist." % (device.name or "")

        self.set_id()  #id = self.id or self.get_uuid()  # only assign a UUID ONCE
        self.signed_by = device
        self.full_clean()  # make sure the model data is of the appropriate types
        self.signature = self.signed_by.get_key().sign(self._hashable_representation())

    @validate_via_booleans
    def validate(self):
        try:
            # if nobody signed it, verification fails
            if not self.signed_by_id:
                raise ValidationError("This model was not signed.")
            # if it's not a trusted device...
            if not self.signed_by.is_trusted():
                if settings.CENTRAL_SERVER:
                    if not self.signed_by.get_zone():
                        raise ValidationError("This model was signed by a Device with no zone, but somehow synced to the central server.")
                elif (_get_own_device().get_zone() is None) + (self.signed_by.get_zone() is None) == 1:
                    # one has a zone, the other doesn't
                    raise ValidationError("This model is on a different zone than this device.")

                elif _get_own_device().get_zone() and not _get_own_device().get_zone().is_member(self.signed_by):
                    # distributed server
                    raise ValidationError("This model is on a different zone than this device.")
            return True
        except ValidationError as ve:
            if settings.DEBUG:  # throw in debug mode, as validation errors should not be happening
                raise ve
            else:
                return False

    def verify(self):
        if not self.validate():
            return False

        # by this point, we know that we're ok with accepting this model from the device that it says signed it
        # now, we just need to check whether or not it is actually signed by that model's private key
        try:
            return self.signed_by.get_key().verify(self._hashable_representation(), self.signature)
        except:
            return False

    @classmethod
    def _hashable_fields(cls, fields=None):

        # if no fields were specified, build a list of all the model's field names
        if not fields:
            fields = [field.name for field in cls._meta.fields if field.name not in cls._unhashable_fields and not hasattr(field, "minversion")]
            # sort the list of fields, for consistency
            fields.sort()

        # certain fields should always be included
        for field in cls._always_hash_fields:
            if field not in fields:
                fields = [field] + fields

        # certain fields should never be included
        fields = [field for field in fields if field not in cls._unhashable_fields]

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

    def save(self, imported=False, increment_counters=True, sign=True, *args, **kwargs):
        """
        Some of the heavy lifting happens here.  There are two saving scenarios:
        (a) We are saving an imported model.
            In this case, we need to make sure that the data check out (but nothing we mark on the object)
        (b) We are saving our own model
            In this case, we need to mark the model with appropriate fields, so that
            it can be sync'd (self.counter), and that it will verify (self.signature)
        """
        if imported:
            # imported models are signed by other devices; make sure they check out
            if not self.signed_by_id:
                raise ValidationError("Imported models must be signed.")
            if not self.verify():
                raise ValidationError("Could not verify the imported model.")  #Imported model's signature did not match.")

            # call the base Django Model save to write to the DB
            super(SyncedModel, self).save(*args, **kwargs)

            # For imported models, we want to keep track of the counter position we're at for that device.
            #   so, if it's ahead of what we had, set it!
            if increment_counters:
                self.signed_by.set_counter_position(self.counter, soft_set=True)


        else:
            # Two critical things to do:
            # 1. local models need to be signed by us
            # 2. and get our counter position

            own_device = _get_own_device()

            if increment_counters:
                self.counter = own_device.increment_counter_position()
            else:
                self.counter = None  # will set this when we sync

            if sign:
                assert self.counter is not None, "Only sign data where count is set"
                # Always sign on the central server.
                self.sign(device=own_device)
            else:
                self.set_id()
                self.signature = None  # make sure the signature will be recomputed on sync

            # call the base Django Model save to write to the DB
            super(SyncedModel, self).save(*args, **kwargs)


    def set_id(self):
        self.id = self.id or self.get_uuid()

    def get_uuid(self):
        """
        By default, all objects get an ID from the
        device and the counter position at which it was created.
        """
        assert self.counter is not None, "counter required for get_uuid"

        own_device = _get_own_device()
        namespace = own_device.id and uuid.UUID(own_device.id) or settings.ROOT_UUID_NAMESPACE
        return uuid.uuid5(namespace, str(self.counter)).hex

    def get_existing_instance(self):
        uuid = self.id or self.get_uuid()
        try:
            return self.__class__.objects.get(id=uuid)
        except self.__class__.DoesNotExist:
            return None


    def get_zone(self):
        """
        Key function for determining which (syncable) objects are associated
        with which zones.
        """
        # some models have a direct zone attribute; try for that
        zone = getattr(self, "zone", None)

        # Otherwise, if it's not yet synced, then get the zone from the local machine
        if not zone and not self.signed_by:
            zone = _get_own_device().get_zone()

        # otherwise, try getting the zone of the device that signed it
        if not zone and self.signed_by:
            zone = self.signed_by.get_zone()

        # otherwise, if it's signed by a trusted authority, try getting the fallback zone
        if not zone and self.signed_by and self.signed_by.is_trusted():
            zone = self.zone_fallback

        return zone
    get_zone.short_description = "Zone"

    def in_zone(self, zone):
        return zone == self.get_zone()


    def __unicode__(self):
        pk = self.pk[0:5] if len(getattr(self, "pk", "")) >= 5 else "[unsaved]"
        signed_by_pk = self.signed_by.pk[0:5] if self.signed_by and self.signed_by.pk else "[None]"
        return u"%s... (Signed by: %s...)" % (pk, signed_by_pk)


class DeferredSignSyncedModel(SyncedModel):
    """
    Synced model that we defer signing until it's time to sync.
    """
    def save(self, sign=settings.CENTRAL_SERVER, *args, **kwargs):
        super(DeferredSignSyncedModel, self).save(*args, sign=sign, **kwargs)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        app_label = "securesync"
        abstract = True


class DeferredCountSyncedModel(DeferredSignSyncedModel):
    """
    Defer incrementing counters until syncing.
    """
    def save(self, increment_counters=settings.CENTRAL_SERVER, *args, **kwargs):
        """
        Note that increment_counters will set counters to None,
        and that if the object must be created, counter will be incremented
        and temporarily set, to create the object ID.
        """
        super(DeferredCountSyncedModel, self).save(*args, increment_counters=increment_counters, **kwargs)

    def set_id(self):
        if self.id:
            pass
        elif self.counter:
            self.id = self.get_uuid()
        else:
            # UUID depends on counter position, so we *have* to get a counter
            #   position to set an id
            own_device = _get_own_device()
            self.counter = own_device.increment_counter_position()
            self.id = self.get_uuid()
            self.counter = None

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        app_label = "securesync"
        abstract = True


class SyncedLog(SyncedModel):
    """
    This is not used, but for backwards compatibility, we need to keep it.
    """
    category = models.CharField(max_length=50)
    value = models.CharField(max_length=250, blank=True)
    data = models.TextField(blank=True)

    class Meta:
        app_label = "securesync"


class ImportPurgatory(ExtendedModel):
    timestamp = models.DateTimeField(auto_now_add=True)
    counter = models.IntegerField()
    retry_attempts = models.IntegerField(default=0)
    model_count = models.IntegerField(default=0)
    serialized_models = models.TextField()
    exceptions = models.TextField()

    class Meta:
        app_label = "securesync"

    def save(self, *args, **kwargs):
        self.counter = self.counter or _get_own_device().get_counter_position()
        super(ImportPurgatory, self).save(*args, **kwargs)

add_syncing_models([SyncedLog])
