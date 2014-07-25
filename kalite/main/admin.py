"""
Manipulating models to expose to admins through the Django admin interface
"""
from django.conf import settings
from django.contrib import admin

from .models import *


class VideoLogAdmin(admin.ModelAdmin):
    list_display = ("video_id", "user", "language", "points", "total_seconds_watched", "complete",)
    list_filter = ("video_id", "user", "language", "complete",)
admin.site.register(VideoLog, VideoLogAdmin)

class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "language", "streak_progress", "complete",)
    list_filter = ("exercise_id", "user", "language", "complete",)
admin.site.register(ExerciseLog, ExerciseLogAdmin)

class UserLogAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled():  # only enable admin if the feature is enabled.
    admin.site.register(UserLog, UserLogAdmin)

class UserLogSummaryAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled() or settings.CENTRAL_SERVER:  # only enable admin if the feature is enabled.
    admin.site.register(UserLogSummary, UserLogSummaryAdmin)

class AttemptLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "language", "answer_given", "context_type", "context_id", "correct")
    list_filter = ("exercise_id", "user", "language", "context_type", "context_id" )
admin.site.register(AttemptLog, AttemptLogAdmin)