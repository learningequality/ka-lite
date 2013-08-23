from django.forms import ModelForm, ChoiceField, RadioSelect

from contact.models import Contact, Deployment, Support, Info, Contribute


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = ('name', 'email', 'org_name', 'org_url', 'type')


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


class ContributeForm(ModelForm):
    class Meta:
        model = Contribute
        fields = ('type','issue',)
