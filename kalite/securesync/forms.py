from django import forms
from models import RegisteredDevicePublicKey, Zone

class RegisteredDevicePublicKeyForm(forms.ModelForm):

    def __init__(self, user, *args, **kwargs):
        super(RegisteredDevicePublicKeyForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['zone'].queryset = reduce(lambda x,y: x+y,
                [orguser.get_zones() for orguser in user.organizationuser_set.all()])

    class Meta:
        model = RegisteredDevicePublicKey
        fields = ("zone", "public_key",)



# class OrganizationForm(forms.ModelForm):
#     class Meta:
#         model = Organization
#         fields = ("name", "description", "url",)
#         widgets = {
#             "name": forms.TextInput(attrs={"size": 70}),
#             "description": forms.Textarea(attrs={"cols": 74, "rows": 2}),
#             "url": forms.TextInput(attrs={"size": 70}),
#         }

