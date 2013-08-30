import re

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from models import RegisteredDevicePublicKey


class RegisteredDevicePublicKeyForm(forms.ModelForm):
    callback_url = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, user, callback_url=None, *args, **kwargs):
        super(RegisteredDevicePublicKeyForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['zone'].queryset = Zone.objects.filter(organization__in=user.organization_set.all())
        self.fields["callback_url"].initial = callback_url

    class Meta:
        model = RegisteredDevicePublicKey
        fields = ("zone", "public_key",)

    def clean_public_key(self):
        public_key = self.cleaned_data["public_key"]
        if RegisteredDevicePublicKey.objects.filter(public_key=public_key).count() > 0:
            raise forms.ValidationError("This public key has already been registered!")
        return public_key
