from django.contrib import admin
from models import *


class VideoLogAdmin(admin.ModelAdmin):
    list_display = ("youtube_id", "user", "seconds_watched", "total_seconds_watched",)
    list_filter = ("youtube_id", "user")
admin.site.register(VideoLog, VideoLogAdmin)


class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "correct", "streak_progress",)
    list_filter = ("exercise_id", "user", "correct",)
admin.site.register(ExerciseLog, ExerciseLogAdmin)

