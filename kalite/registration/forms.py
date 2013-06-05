"""
Forms and validation code for user registration.

"""


from django.contrib.auth.models import User
from django import forms


# I put this on all required fields, because it's easier to pick up
# on them with CSS or JavaScript if they have a class of "required"
# in the HTML. Your mileage may vary. If/when Django ticket #3515
# lands in trunk, this will no longer be necessary.
attrs_dict = { 'class': 'required' }

class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.
    
    """
    username = forms.HiddenInput()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=("Email address"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=("Password (again)"))
    tos1 = forms.BooleanField(required=False)
    tos2 = forms.BooleanField(required=False)
    

    def clean_email(self, email=None):
        """
        Validate that the supplied email address is unique for the
        site.
        
        """
        if not email:
            email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(("You must specify an email address."))
        elif User.objects.filter(email=email.lower()):
            raise forms.ValidationError(("This email address is already in use. Please supply a different email address."))
        elif User.objects.filter(email=email):
            raise forms.ValidationError(("This email address is already in use. Please supply a different email address."))
        return email

        
    def clean_password(self): # NOT CALLED AUTOMATICALLY!
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data.get('password1') != self.cleaned_data.get('password2'):
                raise forms.ValidationError(("The two password fields didn't match."))
        
    def clean_tos1(self):
        if not self.cleaned_data.get('tos1'):
            raise forms.ValidationError(("You must acknowledge having read these terms."))
        return self.cleaned_data.get('tos1')
        
    def clean_tos2(self):
        if not self.cleaned_data.get('tos2'):
            raise forms.ValidationError(("You must acknowledge having read these terms."))
        return self.cleaned_data.get('tos2')

            
    def clean(self):
        #Help docs @ https://docs.djangoproject.com/en/dev/ref/forms/validation/
        import pdb; pdb.set_trace()
        cleaned_data = super(RegistrationForm, self).clean()
        self.clean_email()
        self.clean_password()
        if cleaned_data.get("email"):
            cleaned_data['email'] = cleaned_data.get('email').lower() # always lcase it
            cleaned_data['username'] = cleaned_data.get('email')
        else:
            cleaned_data['username'] = None
        return cleaned_data