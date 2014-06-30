"""
Like django.core.serializers.python, but allows serialization/deserialization based on src/dest version
"""
from django.conf import settings
from django.core.serializers import base
from django.core.serializers.python import Serializer, _get_model
from django.db import models, DEFAULT_DB_ALIAS
from django.utils.encoding import smart_unicode, is_protected_type

from fle_utils.general import version_diff


def Deserializer(object_list, **options):
    """
    Deserialize simple Python objects back into Django ORM instances.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    db = options.pop('using', DEFAULT_DB_ALIAS)

    #
    src_version = options.pop("src_version")  # version that was serialized
    dest_version = options.pop("dest_version")  # version that we're deserializing to
    assert dest_version, "For KA Lite, we should always set the dest version to the current device."

    models.get_apps()
    for d in object_list:
        # Look up the model and starting build a dict of data for it.
        Model = _get_model(d["model"])

        # See comment below for versioned fields; same logic
        #   applies here as well.
        if hasattr(Model, "version"):
            v_diff = version_diff(Model.minversion, dest_version)
            if v_diff > 0 or v_diff is None:
                continue

        data = {Model._meta.pk.attname : Model._meta.pk.to_python(d["pk"])}
        m2m_data = {}

        # Handle each field
        for (field_name, field_value) in d["fields"].iteritems():
            if isinstance(field_value, str):
                field_value = smart_unicode(field_value, options.get("encoding", settings.DEFAULT_CHARSET), strings_only=True)

            try:
                field = Model._meta.get_field(field_name)
            except models.FieldDoesNotExist as fdne:
                # If src version is newer than dest version,
                #   or if it's unknown, then assume that the field
                #   is a new one and skip it.
                # We can't know for sure, because
                #   we don't have that field (we are the dest!),
                #   so we don't know what version it came in on.
                v_diff = version_diff(src_version, dest_version)
                if v_diff > 0 or v_diff is None:
                    continue

                # Something else must be going on, so re-raise.
                else:
                    raise fdne

            # Handle M2M relations
            if field.rel and isinstance(field.rel, models.ManyToManyRel):
                if hasattr(field.rel.to._default_manager, 'get_by_natural_key'):
                    def m2m_convert(value):
                        if hasattr(value, '__iter__'):
                            return field.rel.to._default_manager.db_manager(db).get_by_natural_key(*value).pk
                        else:
                            return smart_unicode(field.rel.to._meta.pk.to_python(value))
                else:
                    m2m_convert = lambda v: smart_unicode(field.rel.to._meta.pk.to_python(v))
                m2m_data[field.name] = [m2m_convert(pk) for pk in field_value]

            # Handle FK fields
            elif field.rel and isinstance(field.rel, models.ManyToOneRel):
                if field_value is not None:
                    if hasattr(field.rel.to._default_manager, 'get_by_natural_key'):
                        if hasattr(field_value, '__iter__'):
                            obj = field.rel.to._default_manager.db_manager(db).get_by_natural_key(*field_value)
                            value = getattr(obj, field.rel.field_name)
                            # If this is a natural foreign key to an object that
                            # has a FK/O2O as the foreign key, use the FK value
                            if field.rel.to._meta.pk.rel:
                                value = value.pk
                        else:
                            value = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                        data[field.attname] = value
                    else:
                        data[field.attname] = field.rel.to._meta.get_field(field.rel.field_name).to_python(field_value)
                else:
                    data[field.attname] = None

            # Handle all other fields
            else:
                data[field.name] = field.to_python(field_value)

        yield base.DeserializedObject(Model(**data), m2m_data)
