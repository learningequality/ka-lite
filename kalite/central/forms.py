from django.forms import ModelForm
from central.models import Organization
from securesync.models import Zone

class OrganizationForm(ModelForm):
	class Meta:
		model = Organization
		fields = ('name', 'description', 'url', 'number', 'address', 'country')


class ZoneForm(ModelForm):
	class Meta:
		model = Zone
		fields = ('name', 'description')