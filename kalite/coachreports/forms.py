from django import forms

from securesync.models import Zone


class DataForm(forms.Form):
    # who?
    facility_id = forms.CharField(max_length=40),
    group_id = forms.CharField(max_length=40),
    user_id = forms.CharField(max_length=40),

    # where?
    topic_path = forms.CharField(max_length=500),
    
    # what?
    xaxis = forms.CharField(max_length=40),
    yaxis = forms.CharField(max_length=40),


class FriendlyForm(forms.Form):
    # who?
    facility_ids = forms.CharField(max_length=40),
    group_ids = forms.CharField(max_length=40),
    user_ids = forms.CharField(),

    exercise_ids = forms.CharField()