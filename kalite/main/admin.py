from django.contrib import admin
from models import *


class VideoLogAdmin(admin.ModelAdmin):
    list_display = ("youtube_id", "user", "points", "total_seconds_watched", "complete",)
    list_filter = ("youtube_id", "user", "complete",)
admin.site.register(VideoLog, VideoLogAdmin)


class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "streak_progress", "complete",)
    list_filter = ("exercise_id", "user", "complete",)
admin.site.register(ExerciseLog, ExerciseLogAdmin)

