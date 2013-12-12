from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext as _

from central.models import Organization, OrganizationInvitation

class OrganizationForm(ModelForm):
    class Meta:
        model = Organization
        fields = ('name', 'description', 'url', 'number', 'address', 'country')


class OrganizationInvitationForm(ModelForm):
    class Meta:
        model = OrganizationInvitation
        fields = ('email_to_invite', 'invited_by', 'organization')
        widgets = {
            'invited_by': forms.HiddenInput(),
            'organization': forms.HiddenInput(),
        }

    def clean(self):
        email_to_invite = self.cleaned_data.get('email_to_invite')
        organization = self.cleaned_data.get('organization')
        user = self.cleaned_data.get('invited_by')

        if not email_to_invite:
            raise forms.ValidationError(_("The email address you entered is invalid."))
        if email_to_invite == user.email:
            raise forms.ValidationError(_("You are already a part of this organization."))
        if OrganizationInvitation.objects.filter(organization=organization, email_to_invite=email_to_invite).count() > 0:
            raise forms.ValidationError(_("You have already sent an invitation email to this user."))

        return self.cleaned_data
