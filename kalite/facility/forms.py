"""
"""
import copy
import re

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from .models import FacilityUser, Facility, FacilityGroup
from fle_utils.django_utils.users import verify_raw_password
from kalite.i18n import get_installed_language_packs, get_language_name, get_default_language


class FacilityUserForm(forms.ModelForm):
    """This form is used for 1) signing up, 2) creating users, and 3) editing users.

    The views contain manual logic for processing passwords (hashing them, etc), so we use
    custom fields here for the "password" and "confirm password" fields.
    """
    password_first   = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password_recheck = forms.CharField(widget=forms.PasswordInput, label=_("Confirm password"))
    default_language = forms.ChoiceField(label=_("Default Language"))
    warned           = forms.BooleanField(widget=forms.HiddenInput, required=False, initial=False)

    def __init__(self, facility, *args, **kwargs):
        super(FacilityUserForm, self).__init__(*args, **kwargs)

        self.fields["default_language"].choices = [(lang_code, get_language_name(lang_code)) for lang_code in get_installed_language_packs()]

        # Select the initial default language,
        #   but only if we're not in the process of updating it to something else.
        if not self.fields["default_language"].initial and "default_language" not in self.changed_data:
            self.fields["default_language"].initial = (self.instance and self.instance.default_language) or get_default_language()

        # Passwords only required on new, not on edit
        self.fields["password_first"].required = self.instance.pk == ""
        self.fields["password_recheck"].required = self.instance.pk == ""

        # Across POST and GET requests
        self.fields["zone_fallback"].initial = facility.get_zone()
        self.fields["facility"].initial = facility
        self.fields["facility"].queryset = Facility.objects.by_zone(facility.get_zone())
        self.fields["group"].queryset = FacilityGroup.objects.filter(facility=facility)

    class Meta:
        model = FacilityUser
        # Note: must preserve order
        fields = ("facility", "group", "username", "first_name", "last_name", "password_first", "password_recheck", "default_language", "is_teacher", "zone_fallback", "warned")
        widgets = {
            "is_teacher": forms.HiddenInput(),
            "zone_fallback": forms.HiddenInput(),
            "warned": forms.HiddenInput(),
            "username": forms.TextInput(attrs={"autocomplete": "off"}),
            "first_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "off"}),
        }


    def set_field_error(self, message, field_name=forms.forms.NON_FIELD_ERRORS):
        self._errors[field_name] = self.error_class(ValidationError(message).messages)
        if field_name in self.cleaned_data:
            del self.cleaned_data[field_name]


    def has_errors(self):
        return bool(self._errors)


    def clean(self):
        facility = self.cleaned_data.get('facility')
        username = self.cleaned_data.get('username', '')
        zone = self.cleaned_data.get('zone_fallback')

        # Don't allow (only through the form) the same username within the same facility, or conflicting with the admin.
        users_with_same_username = FacilityUser.objects.filter(username__iexact=username, facility=facility)
        username_taken = users_with_same_username.count() > 0
        username_changed = not self.instance or self.instance.username != username
        if username_taken and username_changed or User.objects.filter(username__iexact=username).count() > 0:
            self.set_field_error(field_name='username', message=_("A user with this username already exists. Please choose a new username and try again."))

        ## Check password
        password_first = self.cleaned_data.get('password_first', "")
        password_recheck = self.cleaned_data.get('password_recheck', "")
        # If they have put anything in the new password field, it must match the password check field
        if password_first != password_recheck:
            self.set_field_error(field_name='password_recheck', message=_("The passwords didn't match. Please re-enter the passwords."))

        # Next, enforce length if they submitted a password
        if password_first:
            try:
                verify_raw_password(password_first)
            except ValidationError as ve:
                # MUST: The ValidationError constructor sets the error message into a list with
                # `self.messages = [message]` so we get the first message from the list.  It
                # should have assigned the value to `self.message = message` too but maybe on
                # newer Django versions this is fixed.
                message = ''
                if hasattr(ve, 'messages') and isinstance(ve.messages, list) and ve.messages:
                    message = ve.messages[0]
                self.set_field_error(field_name='password_first', message=message)

        elif (self.instance and not self.instance.password) or password_first or password_recheck:
            # Only perform check on a new user or a password change
            if password_first != password_recheck:
                self.set_field_error(field_name='password_recheck', message=_("The passwords didn't match. Please re-enter the passwords."))

        ## Warn the user during sign up or adding user if a user with this first and last name already exists in the facility
        if not self.cleaned_data.get("warned", False) and (self.cleaned_data["first_name"] or self.cleaned_data["last_name"]):
            users_with_same_name = FacilityUser.objects.filter(first_name__iexact=self.cleaned_data["first_name"], last_name__iexact=self.cleaned_data["last_name"]) \
                .filter(Q(signed_by__devicezone__zone=zone) | Q(zone_fallback=zone))  # within the same facility
            if users_with_same_name and (not self.instance or self.instance not in users_with_same_name):
                self.data = copy.deepcopy(self.data)
                self.data["warned"] = self.cleaned_data["warned"] = True
                msg = "%s %s" % (_("%(num_users)d user(s) with first name '%(f_name)s' and last name '%(l_name)s' already exist(s).") % {
                    "num_users": users_with_same_name.count(),
                    "f_name": self.cleaned_data["first_name"],
                    "l_name": self.cleaned_data["last_name"],
                }, _("If you are sure you want to create this user, you may re-submit the form to complete the process."))
                self.set_field_error(message=msg)  # general error, not associated with a field.

        if self.has_errors():
            return self.cleaned_data
        else:
            return super(FacilityUserForm, self).clean()


class FacilityForm(forms.ModelForm):
    name = forms.CharField(label=_("Name (required)"))

    class Meta:
        model = Facility
        fields = ("name", "description", "address", "address_normalized", "latitude", "longitude", "zoom", "contact_name", "contact_phone", "contact_email", "user_count", "zone_fallback", )
        widgets = {
            "zone_fallback": forms.HiddenInput(),
        }

    def clean_user_count(self):
        user_count = self.cleaned_data['user_count']

        if user_count is not None and user_count < 1:
            raise ValidationError(_("User count should should be at least one."), code='invalid_user_count')

        return user_count

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        matching = Facility.objects.by_zone(self.instance.get_zone()).filter(name__iexact=name)
        for model in matching:
            if model.id != self.instance.id:
                raise ValidationError(_("There is already a facility with this name."), code='facility_name_exists')

        return name


class FacilityGroupForm(forms.ModelForm):

    def __init__(self, facility, *args, **kwargs):
        super(FacilityGroupForm, self).__init__(*args, **kwargs)

        # Across POST and GET requests
        self.fields["zone_fallback"].initial = facility.get_zone()
        self.fields["facility"].initial = facility
        self.fields["facility"].queryset = Facility.objects.by_zone(facility.get_zone())

    class Meta:
        model = FacilityGroup
        fields = ("name", "description", "facility", "zone_fallback", )
        widgets = {
            "facility": forms.HiddenInput(),
            "zone_fallback": forms.HiddenInput(), # TODO(jamalex): this shouldn't be in here
        }

    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        ungrouped = re.compile("[uU]+ngrouped")

        if ungrouped.match(name):
            raise forms.ValidationError(_("This group name is reserved. Please choose one without 'ungrouped' in the name."))

        matching = FacilityGroup.objects.filter(facility=self.fields["facility"].initial, name__iexact=name)
        for model in matching:
            if model.id != self.instance.id:
                raise ValidationError(_("There is already a group with this name."), code='group_name_exists')

        return name

