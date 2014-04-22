from django import forms

from kalite.main.topic_tools import get_node_cache

from models import Test

class TestAttemptLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    exercise_id = forms.CharField(max_length=100)
    correct = forms.BooleanField(required=False)  # Allows client to omit this parameter when answer is incorrect.
    random_seed = forms.IntegerField()
    test = forms.ModelChoiceField(queryset=Test.objects)
    index = forms.IntegerField()
    repeat = forms.IntegerField()
    complete = forms.BooleanField(required=False)

    def clean_exercise_id(self):
        """
        Make sure the exercise ID is found.
        """
        if not self.cleaned_data.get("exercise_id", "") in get_node_cache()['Exercise']:
            raise forms.ValidationError(_("Exercise ID not recognized"))