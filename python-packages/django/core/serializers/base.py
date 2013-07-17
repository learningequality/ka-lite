"""
Module for abstract serializer/unserializer base classes.
"""

from StringIO import StringIO

from django.db import models
from django.utils.encoding import smart_unicode


def version_diff(v1, v2):
    """Diff is the integer difference between the most leftward part of the versions that differ.
    If the versions are identical, the method returns zero.
    If v1 is earlier than v2, the method returns negative.
    If v1 is later than v2, the method returns positive.
    If EITHER IS NONE, then we return none.

    Examples:

    version_diff(None, "0.9.4") returns None

    version_diff("0.9.2", "0.9.4") returns -2
    version_diff("0.9.4", "0.9.4") returns 0
    version_diff("0.9.4", "0.9.2") returns 2

    version_diff("0.9", "1.0") returns -1 (0-1)
    version_diff("0.3", "0.7") returns -4 (3-7)

        """


    #
    if v1 is None or v2 is None:
        return None

    v1_parts = v1.split(".")
    v2_parts = v2.split(".")
    if len(v1_parts) != len(v2_parts):
        raise Exception("versions must have the same number of components (periods)")

    for v1p,v2p in zip(v1_parts,v2_parts):
        cur_diff = int(v1p)-int(v2p)
        if cur_diff:
            return cur_diff

    return 0

class SerializerDoesNotExist(KeyError):
    """The requested serializer was not found."""
    pass

class SerializationError(Exception):
    """Something bad happened during serialization."""
    pass

class DeserializationError(Exception):
    """Something bad happened during deserialization."""
    pass

class Serializer(object):
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

        dest_version = options.pop("dest_version", None)  # We're serializing to send to a machine of this version.

        self.start_serialization()
        for obj in queryset:
            # See logic below.  We selectively skip serializing
            #   objects that have a (starting) version greater than the
            #   version we're serializing for.
            v_diff = version_diff(dest_version, getattr(obj, "version", None))
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
                v_diff = version_diff(dest_version, getattr(field, "version", None))
                if field.serialize and (v_diff is None or v_diff >= 0):
                    if field.rel is None:
                        if self.selected_fields is None or field.attname in self.selected_fields:
                            self.handle_field(obj, field)
                    else:
                        if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                            self.handle_fk_field(obj, field)
            for field in concrete_model._meta.many_to_many:
                # "and" condition added by KA Lite.  Logic the same as above.
                v_diff = version_diff(dest_version, getattr(field, "version", None))
                if field.serialize and (v_diff >= 0 or v_diff is None):
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_m2m_field(obj, field)
            self.end_object(obj)
        self.end_serialization()
        return self.getvalue()

    def start_serialization(self):
        """
        Called when serializing of the queryset starts.
        """
        raise NotImplementedError

    def end_serialization(self):
        """
        Called when serializing of the queryset ends.
        """
        pass

    def start_object(self, obj):
        """
        Called when serializing of an object starts.
        """
        raise NotImplementedError

    def end_object(self, obj):
        """
        Called when serializing of an object ends.
        """
        pass

    def handle_field(self, obj, field):
        """
        Called to handle each individual (non-relational) field on an object.
        """
        raise NotImplementedError

    def handle_fk_field(self, obj, field):
        """
        Called to handle a ForeignKey field.
        """
        raise NotImplementedError

    def handle_m2m_field(self, obj, field):
        """
        Called to handle a ManyToManyField.
        """
        raise NotImplementedError

    def getvalue(self):
        """
        Return the fully serialized queryset (or None if the output stream is
        not seekable).
        """
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

class Deserializer(object):
    """
    Abstract base deserializer class.
    """

    def __init__(self, stream_or_string, **options):
        """
        Init this serializer given a stream or a string
        """
        self.options = options
        if isinstance(stream_or_string, basestring):
            self.stream = StringIO(stream_or_string)
        else:
            self.stream = stream_or_string
        # hack to make sure that the models have all been loaded before
        # deserialization starts (otherwise subclass calls to get_model()
        # and friends might fail...)
        models.get_apps()

    def __iter__(self):
        return self

    def next(self):
        """Iteration iterface -- return the next item in the stream"""
        raise NotImplementedError

class DeserializedObject(object):
    """
    A deserialized model.

    Basically a container for holding the pre-saved deserialized data along
    with the many-to-many data saved with the object.

    Call ``save()`` to save the object (with the many-to-many data) to the
    database; call ``save(save_m2m=False)`` to save just the object fields
    (and not touch the many-to-many stuff.)
    """

    def __init__(self, obj, m2m_data=None):
        self.object = obj
        self.m2m_data = m2m_data

    def __repr__(self):
        return "<DeserializedObject: %s.%s(pk=%s)>" % (
            self.object._meta.app_label, self.object._meta.object_name, self.object.pk)

    def save(self, save_m2m=True, using=None):
        # Call save on the Model baseclass directly. This bypasses any
        # model-defined save. The save is also forced to be raw.
        # This ensures that the data that is deserialized is literally
        # what came from the file, not post-processed by pre_save/save
        # methods.
        models.Model.save_base(self.object, using=using, raw=True)
        if self.m2m_data and save_m2m:
            for accessor_name, object_list in self.m2m_data.items():
                setattr(self.object, accessor_name, object_list)

        # prevent a second (possibly accidental) call to save() from saving
        # the m2m data twice.
        self.m2m_data = None
