from django import forms
from django.utils.translation import ugettext as _

class SuperuserForm(forms.Form):
    """Form that represents the schema for superuser creating API requests"""

    superusername = forms.CharField(max_length=40, min_length=1, label='Username', 
        widget=forms.TextInput(attrs={'class':'form-control input-lg', 'placeholder':_('Username')}))

    superpassword = forms.CharField(max_length=40, min_length=1, label='Password', 
        widget=forms.TextInput(attrs={'class':'form-control input-lg', 'placeholder':_('Password')}))

    superemail = forms.EmailField(max_length=40, label='E-mail', 
        widget=forms.TextInput(attrs={'class':'form-control input-lg', 'placeholder':_('E-mail')}))
