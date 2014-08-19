from django.core.exceptions import ValidationError


class BaseFieldMetaclass(type):

    def __init__(cls, name, bases, dict):
        super(BaseFieldMetaclass, cls).__init__(name, bases, dict)


class BaseField(object):
    # __metaclass__ = abc.ABCMeta
    __metaclass__ = BaseFieldMetaclass

    def _set_value(self, *args):
        self._value = args[-1]

    def _get_value(self, *args):
        return self._value

    def __init__(self, *args, **kwargs):
        # set the value to the default provided by the instance argument, or else the field type default
        self._set_value(kwargs.get("default", self._default))


class IntegerField(BaseField):
    _default = 0
    _minimum = float("-Inf")
    _maximum = float("Inf")

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        if "minimum" in kwargs:
            self._minimum = kwargs["minimum"]
        if "maximum" in kwargs:
            self._maximum = kwargs["maximum"]

    def validate(self):
        if not isinstance(self._value, int):
            raise ValidationError("IntegerField value must be of type 'int'.")
        if self._value < self._minimum:
            raise ValidationError("Value for this IntegerField must be greater than %d." % self._minimum)
        if self._value > self._maximum:
            raise ValidationError("Value for this IntegerField must be less than %d." % self._maximum)


class BooleanField(BaseField):
    _default = False

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(*args, **kwargs)

    def validate(self):
        if not isinstance(self._value, bool):
            raise ValidationError("BooleanField value must be of type 'bool'.")


class CharField(BaseField):
    _default = ""
    _max_len = float("Inf")
    _choices = None
    _choice_set = None

    def __init__(self, *args, **kwargs):
        super(CharField, self).__init__(*args, **kwargs)
        if "max_len" in kwargs:
            self._max_len = kwargs["max_len"]
        if "choices" in kwargs:
            self._choices = kwargs["choices"]
            # extract the keys into a set for checking validity efficiently
            self._choice_set = set([choice[0] for choice in self._choices])

    def validate(self):
        if not isinstance(self._value, basestring):
            raise ValidationError("CharField value must be of type 'basestring'.")
        if len(self._value) > self._max_len:
            raise ValidationError("Value for this IntegerField must be less than %d." % self._maximum)
        if self._choices is not None and self._value not in self._choice_set:
            raise ValidationError("Value for this CharField must be one of the following: %s." % ", ".join(self._choice_set))