"""
"""
import datetime
import uuid
import zlib
from pbkdf2 import crypt

from django.conf import settings
from django.contrib.auth.models import check_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Q
from django.db.models.base import ModelBase
from django.db.models.query import QuerySet
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils.text import compress_string
from django.utils.translation import ugettext_lazy as _

from .utils import add_syncing_models
from .. import ID_MAX_LENGTH, IP_MAX_LENGTH
from fle_utils.config.models import Settings
from fle_utils.django_utils.debugging import validate_via_booleans
from fle_utils.django_utils.classes import ExtendedModel


def _get_own_device():
    """
    To allow imports to resolve... the only ugly thing of this code separation.
    """
    from ..devices.models import Device
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
            for model in list(SyncSession.objects.order_by("timestamp")[0:SyncSession.objects.count()-settings.SYNC_SESSIONS_MAX_RECORDS]):
                model.delete()


class SyncedModelQuerySet(QuerySet):

    def soft_delete(self):
        for model in self:
            model.soft_delete()

class SyncedModelManager(models.Manager):

    class Meta:
        app_label = "securesync"

    def __init__(self, show_deleted=None, *args, **kwargs):
        """
        Pass in 'show_deleted=True' to return a model manager that will also show
        deleted objects in the queryset.
        """
        super(SyncedModelManager, self).__init__(*args, **kwargs)

        self.show_deleted = show_deleted is None and getattr(settings, "SHOW_DELETED_OBJECTS", False) or show_deleted

    def get_query_set(self):
        qset = SyncedModelQuerySet(self.model, using=self._db)

        if not self.show_deleted:
            qset = qset.filter(deleted=False)
        return qset

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


class SyncedModelMetaclass(ModelBase):
    """
    This class does the following:
        * adds a signal listener to prevent any deletes from ever happening
        * adds subclasses of SyncedModel to the set of syncing models
    """

    def __init__(cls, name, bases, clsdict):

        if len(cls.mro()) > 4 and not cls._meta.abstract:

            # Add the deletion signal listener.
            if not hasattr(cls, "_do_not_delete_signal"):
                @receiver(pre_delete, sender=cls)
                def disallow_delete(sender, instance, **kwargs):
                    if not getattr(settings, "DEBUG_ALLOW_DELETIONS", False):
                        raise NotImplementedError("Objects of SyncedModel subclasses (like %s) cannot be deleted." % instance.__class__)
                cls._do_not_delete_signal = disallow_delete  # don't let Python destroy this fn on __init__ completion.

                # Add subclass to set of syncing models.
                add_syncing_models([cls])

        super(SyncedModelMetaclass, cls).__init__(name, bases, clsdict)


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

    SyncedModels have a 'soft_delete' method which allows them to be flagged as deleted,
    but not actually be deleted to preserve data. In order to access the deleted objects in queries
    the 'all_objects' model property should be used in place of 'objects'.
    """
    id = models.CharField(primary_key=True, max_length=ID_MAX_LENGTH, editable=False)
    counter = models.IntegerField(default=None, blank=True, null=True)
    signature = models.CharField(max_length=360, blank=True, editable=False, null=True)
    signed_version = models.IntegerField(default=1, editable=False)
    signed_by = models.ForeignKey("Device", blank=True, null=True, related_name="+")
    zone_fallback = models.ForeignKey("Zone", blank=True, null=True, related_name="+")
    deleted = models.BooleanField(default=False)

    objects = SyncedModelManager()
    all_objects = SyncedModelManager(show_deleted=True)

    _unhashable_fields = ("signature", "signed_by") # fields of this class to avoid serializing
    _always_hash_fields = ("signed_version", "id")  # fields of this class to always serialize (see note above for signed_version)
    _import_excluded_validation_fields = tuple()  # fields that should not be validated upon import

    __metaclass__ = SyncedModelMetaclass

    class Meta:
        abstract = True
        app_label = "securesync"

    @transaction.commit_on_success
    def soft_delete(self):
        self.deleted = True  # mark self as deleted

        for related_model in (self._meta.get_all_related_objects()):
            manager = getattr(self, related_model.get_accessor_name())
            related_objects = manager.all()
            for obj in related_objects:
                # Some related objects are SyncedModels, some are not.
                # Try to soft delete so as not to lose syncable data.
                # Fall back to actual deletion if the model does not have a soft_delete method.
                try:
                    obj.soft_delete()  # call this function, not the bulk delete (which we don't have control over, and have disabled)
                except AttributeError:
                    obj.delete()
        self.save()

    def full_clean(self, exclude=None, imported=False):
        """Django method for validating uniqueness constraints.
        We can have uniqueness constraints that can't be expressed as a tuple of fields,
        so need to override this to implement.

        We can also have "soft" uniqueness constraints that may not be used when importing,
        so we add that parameter here.

        Also, when model is deleted, don't validate its foreign keys anymore--they may fail.

        """
        exclude = exclude or []
        if imported:
            exclude = list(set(tuple(exclude) + self._import_excluded_validation_fields))
        if self.deleted:
            exclude = exclude + [f.name for f in self._meta.fields if isinstance(f, models.ForeignKey) ]
        return super(SyncedModel, self).full_clean(exclude=exclude)

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
                # if we are a trusted (zoneless) device, i.e. the central server, then set the zone fallback
                if own_device.is_trusted():
                    self.zone_fallback = self.get_zone()
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
        Replacement default UUID generator that is completely random, rather than being based
        on the signing device id and counter, until we can make the increment_counter_position
        function properly atomic, to avoid having a race condition lead to duplicate counters/IDs.
        """
        return uuid.uuid4().hex
        # The old logic for this method, for reference:
        #  own_device = _get_own_device()
        #  namespace = own_device.id and uuid.UUID(own_device.id) or settings.ROOT_UUID_NAMESPACE
        #  return uuid.uuid5(namespace, str(self.counter)).hex

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
            # trusted machines can set zone arbitrarily; non-trusted cannot
            if _get_own_device().is_trusted() and self.zone_fallback:
                zone = self.zone_fallback
            else:
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
    Synced model that defers signing until it's time to sync. This helps with CPU efficency because
    we don't need to recalculate the model signature every time the model is updated and saved.
    """
    def save(self, sign=None, *args, **kwargs):

        if not sign:
            sign = settings.CENTRAL_SERVER

        super(DeferredSignSyncedModel, self).save(*args, sign=sign, **kwargs)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        app_label = "securesync"
        abstract = True


class DeferredCountSyncedModel(DeferredSignSyncedModel):
    """
    Defer incrementing counters until syncing. This helps with IO efficiency because we don't need to
    update the counter_position on our device's metadata model everytime this model is saved.
    """
    def save(self, increment_counters=None, *args, **kwargs):
        """
        Note that increment_counters will set counters to None,
        and that if the object must be created, counter will be incremented
        and temporarily set, to create the object ID.
        """

        if not increment_counters:
            increment_counters = settings.CENTRAL_SERVER

        super(DeferredCountSyncedModel, self).save(*args, increment_counters=increment_counters, **kwargs)

    def set_id(self):
        self.id = self.id or self.get_uuid()

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
