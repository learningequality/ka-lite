"""
Manipulating models to expose to admins through the Django admin interface
"""
from django.contrib import admin

from .models import *


class VideoLogAdmin(admin.ModelAdmin):
    list_display = ("video_id", "user", "language", "points", "total_seconds_watched", "complete",
                    "completion_timestamp",)
    list_filter = ("completion_timestamp", "complete", "language", "user", "video_id",)
admin.site.register(VideoLog, VideoLogAdmin)


class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "language", "streak_progress", "completion_timestamp", "complete",)
    list_filter = ("completion_timestamp", "complete", "language", "exercise_id", "user",)
admin.site.register(ExerciseLog, ExerciseLogAdmin)


class UserLogAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled():  # only enable admin if the feature is enabled.
    admin.site.register(UserLog, UserLogAdmin)


class UserLogSummaryAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled() or settings.CENTRAL_SERVER:  # only enable admin if the feature is enabled.
    admin.site.register(UserLogSummary, UserLogSummaryAdmin)
