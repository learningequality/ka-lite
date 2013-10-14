import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import FacilityUser, Facility, FacilityGroup


class FacilityUserForm(forms.ModelForm):

    password         = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password_recheck = forms.CharField(widget=forms.PasswordInput, label=_("Confirm password"))

    def __init__(self, facility, *args, **kwargs):
        super(FacilityUserForm, self).__init__(*args, **kwargs)
        self.fields["facility"].initial = facility.id

        # Passwords only required on new, not on edit
        self.fields["password"].required = self.instance.pk == ""
        self.fields["password_recheck"].required = self.instance.pk == ""

        # Across POST and GET requests
        self.fields["group"].queryset = FacilityGroup.objects.filter(facility=facility)
        self.fields["facility"].initial = facility

    class Meta:
        model = FacilityUser
        # Note: must preserve order
        fields = ("facility", "group", "username", "first_name", "last_name", "password", "password_recheck", "is_teacher")
        widgets = {
            "facility": forms.HiddenInput(),
            "is_teacher": forms.HiddenInput(),
        }

    def clean_username(self):
        facility = self.cleaned_data.get('facility', "")
        username = self.cleaned_data.get('username', "")

        # check if given username is unique on both facility users and admins, whatever the casing
        if FacilityUser.objects.filter(username__iexact=username, facility=facility).count() > 0:
            raise forms.ValidationError(_("A user with this username at this facility already exists. Please choose a new username (or select a different facility) and try again."))

        if User.objects.filter(username__iexact=username).count() > 0:
            raise forms.ValidationError(_("The specified username is unavailable. Please choose a new username and try again."))

        return self.cleaned_data['username']

    def clean_password_recheck(self):

        if self.cleaned_data.get('password') != self.cleaned_data.get('password_recheck'):
            raise forms.ValidationError(_("The passwords didn't match. Please re-enter the passwords."))
        return self.cleaned_data['password_recheck']


class FacilityForm(forms.ModelForm):

    class Meta:
        model = Facility
        fields = ("name", "description", "address", "address_normalized", "latitude", "longitude", "zoom", "contact_name", "contact_phone", "contact_email", "user_count",)

    def clean_user_count(self):
        user_count = self.cleaned_data['user_count']
        if user_count < 1:
            raise ValidationError(_('Given user count should not be less than 1'),
                                  code='invalid_user_count')


class FacilityGroupForm(forms.ModelForm):

    class Meta:
        model = FacilityGroup
        fields = ("name",)

    def clean(self):
        name = self.cleaned_data.get("name", "")
        ungrouped = re.compile("[uU]+ngroup")

        if ungrouped.match(name):
            raise forms.ValidationError(_("This group name is reserved. Please choose one without 'ungroup' in the title."))

        return self.cleaned_data


class LoginForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    class Meta:
        model = FacilityUser
        fields = ("facility", "username", "password")

    def __init__(self, request=None, *args, **kwargs):
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['facility'].queryset = Facility.objects.all()

    def clean(self):
        username = self.cleaned_data.get('username', "")
        facility = self.cleaned_data.get('facility', "")
        password = self.cleaned_data.get('password', "")

        # Coerce
        users = FacilityUser.objects.filter(username__iexact=username, facility=facility)
        if users.count() == 1 and users[0].username != username:
            username = users[0].username
            self.cleaned_data['username'] = username

        try:
            self.user_cache = FacilityUser.objects.get(username=username, facility=facility)
        except FacilityUser.DoesNotExist as e:
            raise forms.ValidationError(_("Username was not found for this facility. Did you type your username correctly, and choose the right facility?"))

        if not self.user_cache.check_password(password):
            self.user_cache = None
            if password and "password" not in self._errors:
                self._errors["password"] = self.error_class([_("The password did not match. Please try again.")])

        return self.cleaned_data

    def get_user(self):
        return self.user_cache
