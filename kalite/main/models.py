from django.db import models
from securesync.models import SyncedModel, FacilityUser


class VideoLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    youtube_id = models.CharField(max_length=11, db_index=True)
    seconds_watched = models.IntegerField()
    total_seconds_watched = models.IntegerField(default=0)
    points = models.IntegerField()
    complete = models.BooleanField(default=False)


class ExerciseLog(SyncedModel):
    user = models.ForeignKey(FacilityUser, blank=True, null=True, db_index=True)
    exercise_id = models.CharField(max_length=50, db_index=True)
    answer = models.TextField(blank=True)
    correct = models.BooleanField()
    seed = models.IntegerField(blank=True, null=True)
    streak_progress = models.IntegerField()
    hints_used = models.IntegerField(blank=True, null=True)