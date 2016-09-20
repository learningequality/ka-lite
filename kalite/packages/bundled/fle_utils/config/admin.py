from django.contrib import admin
from models import *


class SettingsAdmin(admin.ModelAdmin):
    list_display = ("name", "value",)        
admin.site.register(Settings, SettingsAdmin)
