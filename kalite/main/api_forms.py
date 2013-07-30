from django import forms


class ExerciseLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    exercise_id = forms.CharField(max_length=100)
    streak_progress = forms.IntegerField()
    points = forms.IntegerField()
    correct = forms.BooleanField()


class VideoLogForm(forms.Form):
    """Form that represents the schema for data API requests"""

    youtube_id = forms.CharField(max_length=25)
    total_seconds_watched = forms.FloatField(required=False)
    seconds_watched = forms.FloatField()
    points = forms.IntegerField()
