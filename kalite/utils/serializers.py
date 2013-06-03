import copy
import json


from django.core import serializers as django_serializers


def version_diff(v1, v2):
    """Diff is the integer difference between the most leftward part of the versions that differ.
    If the versions are identical, the method returns zero."""

    v1_parts = v1.split(".")
    v2_parts = v2.split(".")
    if len(v1_parts) != len(v2_parts):
        raise Exception("versions must have the same number of components (periods)")
    
    for v1p,v2p in zip(v1_parts,v2_parts):
        cur_diff = int(v1p)-int(v2p)
        if cur_diff:
            return cur_diff
    
    return 0
    
    
def serialize(format, queryset, client_version, **options):
    """
    Serialize a queryset (or any iterator that returns database objects) using
    a certain serializer.
    """
    
   # if format != "json":
   #     import pdb; pdb.set_trace()
    
    # Create a dictionary object from the queryset's data 
    #   (essentially creates a deep copy of the object that 
    #   we can safely manipulate)
    obj = json.loads(django_serializers.serialize(format, queryset, **options))

    # Delete any fields with a version too high for the client to handle.
    for qi,q in enumerate(queryset):
        for fi,f in enumerate(q._meta.fields):
            if not hasattr(f, "version"):
                continue
            # property is newer than the client, eliminate it.
            elif version_diff(f.version, client_version)>0:
                del obj[qi]['fields'][f.name]
    
    # Re-serialize back to json
    return json.dumps(obj)

def deserialize(format, stream_or_string, client_version, **options):
    """
    Deserialize a stream or a string. Returns an iterator that yields ``(obj,
    m2m_relation_dict)``, where ``obj`` is a instantiated -- but *unsaved* --
    object, and ``m2m_relation_dict`` is a dictionary of ``{m2m_field_name :
    list_of_related_objects}``.
    """
    #import pdb; pdb.set_trace()
    raise NotImplementedError("Need to check in, then to try on client")
    return django_serializers.deserialize(format, stream_or_string, **options)
