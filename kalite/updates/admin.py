from django.contrib import admin

import settings
from models import *

class UpdateProgressLogAdmin(admin.ModelAdmin):
    list_display = ("process_name", "process_percent", "current_stage", "stage_name", "stage_percent", "total_stages", "completed",)
    list_filter = ("completed",)
admin.site.register(UpdateProgressLog, UpdateProgressLogAdmin)
