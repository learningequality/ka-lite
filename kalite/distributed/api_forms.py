from django import forms

class DateTimeForm(forms.Form):
    """Form that validates DateTimes to be set on the server for the RPi"""

    date_time = forms.DateTimeField()
