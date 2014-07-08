# taken from http://djangosnippets.org/snippets/1200/
from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import capfirst


class MultiSelectFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple
    
    def __init__(self, *args, **kwargs):
        self.max_choices = kwargs.pop('max_choices', 0)
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
        if value and self.max_choices and len(value) > self.max_choices:
            raise forms.ValidationError('You must select a maximum of %s choice%s.'
                    % (apnumber(self.max_choices), pluralize(self.max_choices)))
        return value

class MultiSelectField(models.Field):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_choices_default(self):
        return self.get_choices(include_blank=False)

    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        choicedict = dict(field.choices)

    def formfield(self, **kwargs):
        # don't call super, as that overrides default widget if it has choices
        defaults = {'required': not self.blank, 'label': capfirst(self.verbose_name), 
                    'help_text': self.help_text, 'choices':self.choices}
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectFormField(**defaults)

    def get_db_prep_value(self, value, **kwargs):  # needed to interact with older versions of django
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return ",".join(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def to_python(self, value):
        if isinstance(value, list):
            return value
        elif value==None:
            return ''
        return value.split(",")
    
    def contribute_to_class(self, cls, name):
        super(MultiSelectField, self).contribute_to_class(cls, name)
        if self.choices:
            func = lambda self, fieldname = name, choicedict = dict(self.choices):",".join([choicedict.get(value,value) for value in getattr(self,fieldname)])
            setattr(cls, 'get_%s_display' % self.name, func)

    def validate(self, value, model_instance):
        """
        Extension to properly validate.
        """
        assert self.choices, "Choices must be set."
        if value:
            # Make sure all values are in the acceptable set
            set_diff = set(value) - set([c[0] for c in self.choices])
            if set_diff:
                raise ValidationError("Unrecognized choices: %s" % set_diff)


# Bcipolli: I added this to make database migrations work.
#
# See: http://south.aeracode.org/wiki/MyFieldsDontWork
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^django_snippets\.multiselect\.MultiSelectField"])
