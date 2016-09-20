import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import RegisteredDevicePublicKey, Zone


class RegisteredDevicePublicKeyForm(forms.ModelForm):
    callback_url = forms.CharField(widget=forms.HiddenInput, required=False)
    zone = forms.ChoiceField()

    class Meta:
        model = RegisteredDevicePublicKey
        fields = ("zone", "public_key",)

    def __init__(self, user, callback_url=None, *args, **kwargs):
        super(RegisteredDevicePublicKeyForm, self).__init__(*args, **kwargs)

        # Get the zones
        if user.is_superuser:
            orgs = set([o for z in Zone.objects.all() for o in z.organization_set.all()])
        else:
            orgs = user.organization_set.all()

        # Compute the choices
        orgs = sorted(list(orgs), key=lambda org: org.name.lower())
        self.zone_choices = []
        for org in orgs:
            for zone in sorted(list(org.zones.all()), key=lambda zone: zone.name.lower()):
                selection_text = "%s / %s" % (org.name, zone.name)
                self.zone_choices.append((zone.id, selection_text))

        self.fields['zone'].choices = self.zone_choices
        self.fields["callback_url"].initial = callback_url

    def clean_zone(self):
        """
        Convert back into a valid zone object.
        """
        zone_id = self.cleaned_data["zone"]
        if zone_id not in [tup[0] for tup in self.fields["zone"].choices]:
            raise forms.ValidationError(_("You must select a sharing network from the given choices."))
        try:
            zone = Zone.objects.get(id=zone_id)
        except:
            raise forms.ValidationError(_("You must select a valid sharing network."))
        return zone

    def clean_public_key(self):
        # Some browsers (unclear which) are converting plus signs to spaces during decodeURIComponent
        public_key = self.cleaned_data["public_key"].replace(" ", "+")
        if RegisteredDevicePublicKey.objects.filter(public_key=public_key).count() > 0:
            raise forms.ValidationError(_("This public key has already been registered!"))
        return public_key
