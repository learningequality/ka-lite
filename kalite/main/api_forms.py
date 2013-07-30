from django import forms

from main.topicdata import ID2SLUG_MAP, NODE_CACHE


class ExerciseLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    exercise_id = forms.CharField(max_length=100)
    streak_progress = forms.IntegerField()
    points = forms.IntegerField()
    correct = forms.BooleanField(required=False)  # Allows client to omit this parameter when answer is incorrect.

    def clean_exercise_id(self):
        """
        Make sure the exercise ID is found.
        """
        if not self.cleaned_data.get("exercise_id", "") in NODE_CACHE['Exercise']:
            raise forms.ValidationError(_("Exercise ID not recognized"))


class VideoLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    youtube_id = forms.CharField(max_length=25)
    total_seconds_watched = forms.FloatField(required=False)
    seconds_watched = forms.FloatField()
    points = forms.IntegerField()

    def clean_youtube_id(self):
        """
        Make sure the youtube ID is found.
        """
        if not self.cleaned_data.get("youtube_id", "") in ID2SLUG_MAP:
            raise forms.ValidationError(_("Youtube ID not recognized."))

