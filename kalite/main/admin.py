from django.contrib import admin

import settings
from models import *

class VideoLogAdmin(admin.ModelAdmin):
    list_display = ("youtube_id", "user", "points", "total_seconds_watched", "complete",)
    list_filter = ("youtube_id", "user", "complete",)
admin.site.register(VideoLog, VideoLogAdmin)

class ExerciseLogAdmin(admin.ModelAdmin):
    list_display = ("exercise_id", "user", "streak_progress", "complete",)
    list_filter = ("exercise_id", "user", "complete",)
admin.site.register(ExerciseLog, ExerciseLogAdmin)

class UserLogAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled():  # only enable admin if the feature is enabled.
    admin.site.register(UserLog, UserLogAdmin)

class UserLogSummaryAdmin(admin.ModelAdmin):
    pass
if UserLog.is_enabled() or settings.CENTRAL_SERVER:  # only enable admin if the feature is enabled.
    admin.site.register(UserLogSummary, UserLogSummaryAdmin)
