from django.db import models
from securesync.models import SyncedModel, FacilityUser


class VideoLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True)
    youtube_id = models.CharField(max_length=11)
    seconds_watched = models.IntegerField()
    total_seconds_watched = models.IntegerField(default=0)


class ExerciseLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True)
    exercise_id = models.CharField(max_length=50)
    answer = models.TextField(blank=True)
    correct = models.BooleanField()
    seed = models.IntegerField(blank=True, null=True)
    streak_progress = models.IntegerField()
    hints_used = models.IntegerField(blank=True, null=True)