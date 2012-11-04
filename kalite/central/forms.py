from django.forms import ModelForm
from central.models import Organization

class OrganizationForm(ModelForm):
	class Meta:
		model = Organization
		fields = ('name', 'description', 'url', 'number', 'address', 'country')
