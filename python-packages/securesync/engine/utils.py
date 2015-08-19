"""
Used for labeling models that use securesync.
This is where the heavy lifting happens!
"""
import logging
from annoying.functions import get_object_or_None

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.fields.related import ForeignKey

from .. import VERSION
from fle_utils.django_utils import serializers


_syncing_models = []  # all models we want to sync


def add_syncing_models(models, dependency_check=False):
    """When sync is run, these models will be sync'd"""

    get_foreign_key_classes = lambda m: set([field.rel.to for field in m._meta.fields if isinstance(field, ForeignKey)])

    for model in models:
        if model in _syncing_models:
            logging.debug("We are already syncing model %s; likely from different ways of importing the same models file." % unicode(model))
            continue

        # When we add models to be synced, we need to make sure
        #   that models that depend on other models are synced AFTER
        #   the model it depends on has been synced.

        # Get the dependencies of the new model
        foreign_key_classes = get_foreign_key_classes(model)

        # Find all the existing models that this new model refers to.
        class_indices = [_syncing_models.index(cls) for cls in foreign_key_classes if cls in _syncing_models]

        # Insert just after the last dependency found,
        #   or at the front if no dependencies
        insert_after_idx = 1 + (max(class_indices) if class_indices else -1)

        # Before inserting, make sure that any models referencing *THIS* model
        # appear after this model.
        if dependency_check and [True for synmod in _syncing_models[0:insert_after_idx-1] if model in get_foreign_key_classes(synmod)]:
            raise Exception("Dependency loop detected in syncing models; cannot proceed.")

        # Now we're ready to insert.
        _syncing_models.insert(insert_after_idx + 1, model)


def get_device_counters(**kwargs):
    """Get device counters, filtered by zone"""
    assert ("zone" in kwargs) + ("devices" in kwargs) == 1, "Must specify zone or devices, and not both."

    from ..devices.models import Device
    devices = kwargs.get("devices") or Device.all_objects.by_zone(kwargs["zone"])  # include deleted objects

    device_counters = {}
    for device in list(devices):
        if device.id not in device_counters:  # why is this needed?
            device_counters[device.id] = device.get_counter_position()

            # The local device may have items that haven't incremented the device counter,
            #   but instead have deferred until sync time.  Include those!
            if device.is_own_device():
                cnt = 0
                for Model in _syncing_models:
                    cnt += Model.all_objects.filter(Q(counter__isnull=True) | Q(signature__isnull=True)).count()  # include deleted records
                device_counters[device.id] += cnt

    return device_counters


def get_models(device_counters=None, limit=None, zone=None, dest_version=None, **kwargs):
    """Serialize models for some intended version (dest_version)
    Default is our own version--i.e. include all known fields.
    If serializing for a device of a lower version, pass in that device's version!
    """
    limit = limit or settings.SYNCING_MAX_RECORDS_PER_REQUEST  # must be specified

    from ..devices.models import Device # cannot be top-level, otherwise inter-dependency of this and models fouls things up
    own_device = Device.get_own_device()

    # Get the current version if none was specified
    if not dest_version:
        dest_version = own_device.get_version()

    # use the current device's zone if one was not specified
    if not zone:
        assert (not settings.CENTRAL_SERVER), "get_models should always be called with a zone, on the central server."
        zone = own_device.get_zone()

    # if no devices specified, assume we're starting from zero, and include all devices in the zone
    if device_counters is None:
        device_counters = dict((device.id, 0) for device in Device.all_objects.by_zone(zone))  # include deleted devices

    # remove all requested devices that either don't exist or aren't in the correct zone
    for device_id in device_counters.keys():
        device = get_object_or_None(Device.all_objects, pk=device_id)
        if not device or not (device.in_zone(zone) or device.is_trusted()):
            del device_counters[device_id]

    models = []
    remaining = limit

    # loop through all the model classes marked as syncable
    #  (note: NEVER BREAK OUT OF THIS LOOP!  We need to ensure that
    #    all models below the counter position selected are sent NOW,
    #    otherwise they will be forgotten FOREVER)
    for Model in _syncing_models:

        # loop through each of the devices of interest
        #   Do devices first, because each device is independent.
        #   Models within a device are highly dependent (on explicit dependencies,
        #   as well as counter position)
        for device_id, counter in device_counters.items():
            # We need to track the min counter position (send things above this value)
            #   and the max (we're sending up to this value, so make sure nothing
            #   below it is left behind)
            counter_min = counter + 1
            counter_max = 0

            device = Device.all_objects.get(pk=device_id)

            queryset = Model.all_objects.filter(Q(signed_by=device) | Q(signed_by__isnull=True) | Q(counter__isnull=True))

            # for trusted (central) device, only include models with the correct fallback zone
            if not device.in_zone(zone):
                assert device.is_trusted(), "Should never include devices not ACTUALLY in the zone, except trusted devices."
                queryset = queryset.filter(zone_fallback=zone)

            # Now select relevant items that have been updated since the last sync event
            queryset = queryset.filter(Q(counter__gte=counter_min) | Q(counter__isnull=True))
            if not queryset:
                continue

            # Make sure you send anything that HAS to be sent (i.e. send anything that is BELOW
            #   the max counter position that we do plan to send.  If we find things that we
            #   unexpectedly need to send, make sure to add room for them.

            if remaining is None: # this means limit was None, so we just sync everything
                new_models = queryset
            else:
                if counter_max is None:
                    # If we're sending something with counter=None, then this will set
                    #   the devicecounter above anything downstream, so these downstream items
                    #   must be sent NOW
                    remaining += max(0, (queryset.filter(counter__isnull=False).count() - remaining))
                else:
                    # If we're sending something with counter=10, then anything with a lower
                    #   counter must be sent along with it.  So, squeeze it in
                    remaining += max(0, (queryset.filter(counter__lt=counter_max).count() - remaining))

                # Grab up to (remaining) model instances, then decrease the remaining to the total limit remaining
                new_models = queryset[:remaining]

            if not new_models:
                continue

            if counter_max is not None:
                # None is the most severe, so only check if we're not already sending things with None
                counters = [m.counter for m in new_models]
                if None in counters:
                    counter_max = None
                else:
                    counter_max = max(counter_max, max(counters))

            models += new_models
            if remaining is not None:
                remaining -= len(new_models)

        # Must loop through all models (due to potential dependencies), but
        if remaining is not None and remaining <= 0:
            break

    return models


def get_serialized_models(*args, **kwargs):
    from ..devices.models import Device

    models = get_models(*args, **kwargs)

    dest_version = kwargs.get("dest_version") or Device.get_own_device().get_version()
    include_count = kwargs.get("include_count", False)
    verbose = kwargs.get("verbose", False)

    # serialize the models we found
    serialized_models = serialize(models, ensure_ascii=False, dest_version=dest_version)

    if verbose:
        for model in models:
            print "EXPORTED %s (id: %s, counter: %d, signed_by: %s)" % (model.__class__.__name__, model.id[0:5], model.counter, model.signed_by.id[0:5])

    if include_count:
        return {"models": serialized_models, "count": len(models)}
    else:
        return serialized_models


#@transaction.commit_on_success
def save_serialized_models(data, increment_counters=True, src_version=None, verbose=False):
    """Unserializes models (from a device of version=src_version) in data and saves them to the django database.
    If src_version is None, all unrecognized fields are (silently) stripped off.
    If it is set to some value, then only fields of versions higher than ours are stripped off.
    By defaulting to src_version=None, we're expecting a perfect match when we come in
    (i.e. that wherever we got this data from, they were smart enough to "dumb it down" for us,
    or they were old enough to have nothing unexpected)

    So, care must be taken in calling this function

    Returns a dictionary of the # of saved models, # unsaved, and any exceptions during saving"""

    from .models import ImportPurgatory # cannot be top-level, otherwise inter-dependency of this and models fouls things up
    from ..devices.models import Device

    own_device = Device.get_own_device()
    if not src_version:  # default version: our own
        src_version = own_device.get_version()

    # if data is from a purgatory object, load it up
    if isinstance(data, ImportPurgatory):
        purgatory = data
        data = purgatory.serialized_models
    else:
        purgatory = None

    # deserialize the models, either from text or a list of dictionaries
    if isinstance(data, str) or isinstance(data, unicode):
        models = deserialize(data, src_version=src_version, dest_version=own_device.get_version())
    else:
        models = deserialize(data, src_version=src_version, dest_version=own_device.get_version())

    # try importing each of the models in turn
    unsaved_models = []
    exceptions = ""
    saved_model_count = 0
    try:
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
                model.full_clean(imported=True)

                # save the imported model (checking that the signature is valid in the process)
                model.save(imported=True, increment_counters=increment_counters)

                # keep track of how many models have been successfully saved
                saved_model_count += 1

                if verbose:
                    print "IMPORTED %s (id: %s, counter: %d, signed_by: %s)" % (model.__class__.__name__, model.id[0:5], model.counter, model.signed_by.id[0:5])

            except ValidationError as e: # the model could not be saved

                # keep a running list of models and exceptions, to be stored in purgatory
                exceptions += "%s: %s\n" % (model.pk, e)
                unsaved_models.append(model)

                # if the model is at least properly signed, try incrementing the counter for the signing device
                # (because otherwise we may never ask for additional models)
                try:
                    if increment_counters and model.verify():
                        model.signed_by.set_counter_position(model.counter, soft_set=True)
                except:
                    pass

    except Exception as e:
        exceptions += unicode(e)

    # deal with any models that didn't validate properly; throw them into purgatory so we can try again later
    if unsaved_models:
        if not purgatory:
            purgatory = ImportPurgatory()

        # These models were successfully unserialized, so re-save in our own version.
        purgatory.serialized_models = serialize(unsaved_models, ensure_ascii=False, dest_version=own_device.get_version())
        purgatory.exceptions = exceptions
        purgatory.model_count = len(unsaved_models)
        purgatory.retry_attempts += 1
        purgatory.save()
    elif purgatory: # everything saved properly this time, so we can eliminate the purgatory instance
        purgatory.delete()

    out_dict = {
        "unsaved_model_count": len(unsaved_models),
        "saved_model_count": saved_model_count,
    }
    if exceptions:
        out_dict["exceptions"] = exceptions

    return out_dict


def serialize(models, sign=True, increment_counters=True, dest_version=VERSION, *args, **kwargs):
    """
    This function encapsulates serialization, and ensures that any final steps needed before syncing
    (e.g. signing, incrementing counters, etc) are done.
    """
    from .models import SyncedModel
    from ..devices.models import Device
    own_device = Device.get_own_device()

    for model in models:
        resave = False

        if increment_counters or sign:
            assert isinstance(model, SyncedModel), "Can only serialize SyncedModel instances"

        if increment_counters and not model.counter:
            model.counter = own_device.increment_counter_position()
            resave = True

        if sign and not model.signature:
            model.sign()
            resave = True

        if resave:
            super(SyncedModel, model).save()

    return serializers.serialize("versioned-json", models, dest_version=dest_version, *args, **kwargs)


def deserialize(data, src_version=VERSION, dest_version=VERSION, *args, **kwargs):
    """
    Similar to serialize, except for deserialization.
    """
    return serializers.deserialize("versioned-json", data, src_version=src_version, dest_version=dest_version, *args, **kwargs)
