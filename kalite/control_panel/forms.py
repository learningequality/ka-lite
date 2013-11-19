from django import forms
from django.forms import ModelForm

from securesync.models import Zone


class ZoneForm(ModelForm):
    class Meta:
        model = Zone
        fields = ('name', 'description')

class UploadFileForm(forms.Form):
    file  = forms.FileField()

class DateRangeForm(forms.Form):
    """Form that validates Dates for CSV Export"""

    period_start = forms.DateField()
    period_end = forms.DateField()