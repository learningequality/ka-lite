from django import forms

from .topic_tools import get_node_cache


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
        if not self.cleaned_data.get("exercise_id", "") in get_node_cache('Exercise'):
            raise forms.ValidationError(_("Exercise ID not recognized"))


class VideoLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    video_id = forms.CharField(max_length=100)
    youtube_id = forms.CharField(max_length=20)
    total_seconds_watched = forms.FloatField(required=False)
    seconds_watched = forms.FloatField(required=False)
    points = forms.IntegerField()

    def clean_video_id(self):
        """
        Make sure the video ID is found.
        """
        if self.cleaned_data["video_id"] not in get_node_cache("Video"):
            raise forms.ValidationError(_("Video ID not recognized."))

class DateTimeForm(forms.Form):
    """Form that validates DateTimes to be set on the server for the RPi"""

    date_time = forms.DateTimeField()
