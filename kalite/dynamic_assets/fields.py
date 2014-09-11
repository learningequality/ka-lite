from django.core.exceptions import ValidationError


class BaseField(object):
    def __init__(self, *args, **kwargs):
        if self.__class__ == BaseField:
            raise NotImplementedError("A BaseField cannot be instantiated directly, only subclasses can.")
        if "default" in kwargs:
            self._default = kwargs["default"]


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

    def validate(self, value):
        if type(value) != int:
            raise ValidationError("IntegerField value must be of type 'int'.")
        if value < self._minimum:
            raise ValidationError("Value for this IntegerField must be greater than %d." % self._minimum)
        if value > self._maximum:
            raise ValidationError("Value for this IntegerField must be less than %d." % self._maximum)


class BooleanField(BaseField):
    _default = False

    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(*args, **kwargs)

    def validate(self, value):
        if type(value) != bool:
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

    def validate(self, value):
        if not isinstance(value, basestring):
            raise ValidationError("CharField value must be of type 'basestring'.")
        if len(value) > self._max_len:
            raise ValidationError("Value for this IntegerField must be less than %d." % self._maximum)
        if self._choices is not None and value not in self._choice_set:
            raise ValidationError("Value for this CharField must be one of the following: %s." % ", ".join(self._choice_set))