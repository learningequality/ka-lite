import re

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from models import RegisteredDevicePublicKey, Zone


class RegisteredDevicePublicKeyForm(forms.ModelForm):
    callback_url = forms.CharField(widget=forms.HiddenInput(), required=False)
    zone = forms.ChoiceField()

    class Meta:
        model = RegisteredDevicePublicKey
        fields = ("zone", "public_key",)

    def __init__(self, user, callback_url=None, *args, **kwargs):
        super(RegisteredDevicePublicKeyForm, self).__init__(*args, **kwargs)

        # Get the zones
        if user.is_superuser:
            self.zones = Zone.objects.all()
            self.orgs = set([o for z in self.zones for o in z.organization_set.all()])
        else:
            self.orgs = user.organization_set.all()
            self.zones = Zone.objects.filter(organization__in=self.orgs)

        # Compute the choices
        self.zone_choices = []
        for zone in self.zones.order_by("name"):
            org_name = zone.organization_set.all()[0] if zone.organization_set.count() > 0 else "[Headless]"
            selection_text = "%s (%s)" % (zone.name, org_name) if len(self.orgs) > 1 else zone.name
            self.zone_choices.append((zone.id, selection_text))

        self.fields['zone'].choices = self.zone_choices
        self.fields["callback_url"].initial = callback_url

    def clean_zone(self):
        """
        Convert back into a valid zone object.
        """
        zone_id = self.cleaned_data["zone"]
        if zone_id not in [tup[0] for tup in self.fields["zone"].choices]:
            raise forms.ValidationError("You must select a zone from the given choices.")
        try:
            zone = Zone.objects.get(id=zone_id)
        except:
            raise forms.ValidationError("You must select a valid Zone.")
        return zone

    def clean_public_key(self):
        public_key = self.cleaned_data["public_key"]
        if RegisteredDevicePublicKey.objects.filter(public_key=public_key).count() > 0:
            raise forms.ValidationError("This public key has already been registered!")
        return public_key
