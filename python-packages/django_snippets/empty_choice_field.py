"""
Modified from https://gist.github.com/davidbgk/651080
via http://stackoverflow.com/questions/14541074/empty-label-choicefield-django
"""
from django import forms
from django.utils.translation import ugettext as _

class EmptyChoiceField(forms.ChoiceField):
    def __init__(self, choices, empty_label=_("(Please select a category)"), *args, **kwargs):
 
        # prepend an empty label
        choices = tuple([(u'', empty_label)] + list(choices))
 
        super(EmptyChoiceField, self).__init__(choices=choices, *args, **kwargs)