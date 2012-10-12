from django import forms
from models import Organization


# class OrganizationForm(forms.ModelForm):
#     class Meta:
#         model = Organization
#         fields = ("name", "description", "url",)
#         widgets = {
#             "name": forms.TextInput(attrs={"size": 70}),
#             "description": forms.Textarea(attrs={"cols": 74, "rows": 2}),
#             "url": forms.TextInput(attrs={"size": 70}),
#         }

