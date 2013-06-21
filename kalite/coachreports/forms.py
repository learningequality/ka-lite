from django import forms


class DataForm(forms.Form):
    """Form that represents the schema for data API requests"""
    
    # who?
    facility_id = forms.CharField(max_length=40),
    group_id = forms.CharField(max_length=40),
    user_id = forms.CharField(max_length=40),

    # where?
    topic_path = forms.CharField(max_length=500),
    
    # what?
    xaxis = forms.CharField(max_length=40),
    yaxis = forms.CharField(max_length=40),
