from django.forms import ModelForm
from contact.models import Contact, Deployment, Support, Info


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = ('type', 'name', 'email', 'org_name', 'org_url','user')
        hidden = ('user')
        
class DeploymentForm(ModelForm):
    class Meta:
        model = Deployment
        fields = ('countries', 'internet_access', 'hardware_infrastructure', 'facilities', 'low_cost_bundle', 'other' )
        
class SupportForm(ModelForm):
    class Meta:
        model = Support
        fields = ('type', 'issue')
        
class InfoForm(ModelForm):
    class Meta:
        model = Info
        fields = ('issue',)
