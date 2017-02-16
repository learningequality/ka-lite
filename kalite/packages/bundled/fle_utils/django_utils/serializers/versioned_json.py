"""
Like django.core.serializers.json, but allows serialization/deserialization based on src/dest version
"""
import datetime
import decimal
from StringIO import StringIO

from django.core.serializers import json
from django.core.serializers.base import DeserializationError
from django.db import models
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.timezone import is_aware

from .versioned_python import Deserializer as PythonDeserializer
from fle_utils.general import version_diff


class Serializer(json.Serializer):
    """
    Abstract serializer base class.
    """

    # Indicates if the implemented serializer is only available for
    # internal Django use.
    internal_use_only = False

    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", StringIO())
        self.selected_fields = options.pop("fields", None)
        self.use_natural_keys = options.pop("use_natural_keys", False)

        dest_version = options.pop("dest_version")  # We're serializing to send to a machine of this version.

        self.start_serialization()
        self.first = True
        for obj in queryset:
            # See logic below.  We selectively skip serializing
            #   objects that have a (starting) version greater than the
            #   version we're serializing for.
            v_diff = version_diff(dest_version, getattr(obj, "minversion", None))
            if v_diff is not None and v_diff < 0:
                continue

            self.start_object(obj)
            # Use the concrete parent class' _meta instead of the object's _meta
            # This is to avoid local_fields problems for proxy models. Refs #17717.
            concrete_model = obj._meta.concrete_model
            for field in concrete_model._meta.local_fields:

                # "and" condition added by KA Lite.
                #
                # Serialize the field UNLESS all of the following are true:
                #   * we've passed in a specific dest_version
                #   * the field is marked with a version
                #   * that version is later than the dest_version
                v_diff = version_diff(dest_version, getattr(field, "minversion", None))
                if field.serialize and (v_diff is None or v_diff >= 0):
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in concrete_model._meta.many_to_many:
                # "and" condition added by KA Lite.  Logic the same as above.
                v_diff = version_diff(dest_version, getattr(field, "minversion", None))
                if field.serialize and (v_diff >= 0 or v_diff is None):
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)

            self.first = False

        self.end_serialization()
        return self.getvalue()


def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.

    Note: no change from Django version,
      but needed to import here to use the versioned python deserializer
      (see the import at the top for PythonDeserializer)
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    try:
        for obj in PythonDeserializer(simplejson.load(stream), **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception, e:
        # Map to deserializer error
        raise DeserializationError(e)
