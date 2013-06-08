from django import forms
from models import RegisteredDevicePublicKey, Zone, FacilityUser, Facility, FacilityGroup
from django.utils.translation import ugettext_lazy as _
import re


class RegisteredDevicePublicKeyForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(RegisteredDevicePublicKeyForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['zone'].queryset = Zone.objects.filter(organization__in=user.organization_set.all())

    class Meta:
        model = RegisteredDevicePublicKey
        fields = ("zone", "public_key",)
        
    def clean_public_key(self):
        public_key = self.cleaned_data["public_key"]
        if RegisteredDevicePublicKey.objects.filter(public_key=public_key).count() > 0:
            raise forms.ValidationError("This public key has already been registered!")
        return public_key
        

class FacilityUserForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))    
    
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(FacilityUserForm, self).__init__(*args, **kwargs)
    
    class Meta:
        model = FacilityUser
        fields = ("facility", "group", "username", "first_name", "last_name",)
        widgets = {
            'facility': forms.HiddenInput(),
        }

    def clean(self):
        facility = self.cleaned_data.get('facility')
        username = self.cleaned_data.get('username')
        self.cleaned_data["username"] = username.lower() #lcase it, but validate both to avoid collision
        
        # Now validate again, as lowercase
        if FacilityUser.objects.filter(username=username.lower(), facility=facility).count() > 0:
            raise forms.ValidationError(_("A user with this username at this facility already exists. Please choose a new username (or select a different facility) and try again."))

        if FacilityUser.objects.filter(username=username, facility=facility).count() > 0:
            raise forms.ValidationError(_("A user with this username at this facility already exists. Please choose a new username (or select a different facility) and try again."))


        return self.cleaned_data

    
class FacilityTeacherForm(FacilityUserForm):

    class Meta:
        model = FacilityUser
        fields = ("facility", "username", "first_name", "last_name",)
        widgets = {
            'facility': forms.HiddenInput(),
        }

class FacilityForm(forms.ModelForm):

    class Meta:
        model = Facility
        fields = ("name", "description", "address", "address_normalized", "latitude", "longitude", "zoom", "contact_name", "contact_phone", "contact_email", "user_count",)

        
class FacilityGroupForm(forms.ModelForm):

    class Meta:
        model = FacilityGroup
        fields = ("name",)
        
    def clean(self):
        name = self.cleaned_data.get("name")
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
        username = self.cleaned_data.get('username')
        facility = self.cleaned_data.get('facility')
        password = self.cleaned_data.get('password')

        try:
            self.user_cache = FacilityUser.objects.get(username=username.lower(), facility=facility)
            username = username.lower()
            self.cleaned_data['username'] = username
        except FacilityUser.DoesNotExist as e:
            # now try again, with lcased username        
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

