"""
Used for labeling models that use securesync.  This is where the heavy lifting happens!
"""
from annoying.functions import get_object_or_None

from django.core.exceptions import ValidationError

import settings
import version
from settings import LOG as logging
from shared import serializers

_syncing_models = [] # all models we want to sync


def add_syncing_models(models):
    """When sync is run, these models will be sync'd"""
    for model in models:
        if model in _syncing_models:
            logging.warn("We are already syncing model %s" % str(model))
        else:
            _syncing_models.append(model)

def get_syncing_models():
    return _syncing_models

    
def get_serialized_models(device_counters=None, limit=100, zone=None, include_count=False, dest_version=version.VERSION):
    """Serialize models for some intended version (dest_version)
    Default is our own version--i.e. include all known fields.
    If serializing for a device of a lower version, pass in that device's version!
    """
    from models import Device # cannot be top-level, otherwise inter-dependency of this and models fouls things up

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
        for Model in _syncing_models:

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
    serialized_models = serializers.serialize("versioned-json", models, ensure_ascii=False, dest_version=dest_version)

    if include_count:
        return {"models": serialized_models, "count": len(models)}
    else:
        return serialized_models


def save_serialized_models(data, increment_counters=True, src_version=version.VERSION):
    """Unserializes models (from a device of version=src_version) in data and saves them to the django database.
    If src_version is None, all unrecognized fields are (silently) stripped off.  
    If it is set to some value, then only fields of versions higher than ours are stripped off.
    By defaulting to src_version=None, we're expecting a perfect match when we come in
    (i.e. that wherever we got this data from, they were smart enough to "dumb it down" for us,
    or they were old enough to have nothing unexpecting)

    So, care must be taken in calling this function

    Returns a dictionary of the # of saved models, # unsaved, and any exceptions during saving"""
    
    from models import ImportPurgatory # cannot be top-level, otherwise inter-dependency of this and models fouls things up

    # if data is from a purgatory object, load it up
    if isinstance(data, ImportPurgatory):
        purgatory = data
        data = purgatory.serialized_models
    else:
        purgatory = None

    # deserialize the models, either from text or a list of dictionaries
    if isinstance(data, str) or isinstance(data, unicode):
        models = serializers.deserialize("versioned-json", data, src_version=src_version, dest_version=version.VERSION)
    else:
        models = serializers.deserialize("versioned-python", data, src_version=src_version, dest_version=version.VERSION)

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
        
    except Exception as e:
        exceptions += str(e)
        
    # deal with any models that didn't validate properly; throw them into purgatory so we can try again later
    if unsaved_models:
        if not purgatory:
            purgatory = ImportPurgatory()
        
        # These models were successfully unserialized, so re-save in our own version.
        purgatory.serialized_models = serializers.serialize("versioned-json", unsaved_models, ensure_ascii=False, dest_version=version.VERSION)
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
