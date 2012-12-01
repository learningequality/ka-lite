from django import forms
from django.forms import ModelForm
from central.models import Organization, OrganizationInvitation
from securesync.models import Zone

class OrganizationForm(ModelForm):
	class Meta:
		model = Organization
		fields = ('name', 'description', 'url', 'number', 'address', 'country')


class ZoneForm(ModelForm):
	class Meta:
		model = Zone
		fields = ('name', 'description')


class OrganizationInvitationForm(ModelForm):
	class Meta:
		model = OrganizationInvitation
		fields = ('email_to_invite', 'invited_by', 'organization')
		widgets = {
            'invited_by': forms.HiddenInput(),
            'organization': forms.HiddenInput(),
        }