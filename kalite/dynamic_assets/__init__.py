from django.core.exceptions import ValidationError

from . import fields

class DynamicSettingsMetaclass(type):

    def __init__(cls, name, bases, dict):
        super(DynamicSettingsMetaclass, cls).__init__(name, bases, dict)
        cls._fields = {}
        for name, field in dict.items():

            if isinstance(field, fields.BaseField):

                # add it to the list of fields
                cls._fields[name] = field

                # turn the attribute itself into a property for accessing the value
                setattr(cls, name, property(field._get_value, field._set_value))


class DynamicSettingsBase(object):

    __metaclass__ = DynamicSettingsMetaclass

    def validate(self):
        # validate all fields individually, and consolidate errors into a single error
        errors = {}
        for key, field in self._fields.items():
            try:
                field.validate()
            except ValidationError as e:
                errors[key] = e.messages
        if errors:
            raise ValidationError(errors)

    def to_json(self):
        return dict([(key, getattr(self, key)) for key in self._fields.keys()])
