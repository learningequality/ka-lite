from django.contrib import admin

from models import *

class UpdateProgressLogAdmin(admin.ModelAdmin):
    list_display = ("process_name", "process_percent", "current_stage", "stage_name", "stage_percent", "total_stages", "completed",)
    list_filter = ("completed",)
admin.site.register(UpdateProgressLog, UpdateProgressLogAdmin)

class VideoFileAdmin(admin.ModelAdmin):
    list_display = ("youtube_id", "flagged_for_download", "download_in_progress", "cancel_download", "percent_complete",)
    list_filter = ("flagged_for_download", "download_in_progress",)
admin.site.register(VideoFile, VideoFileAdmin)
