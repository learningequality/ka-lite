from django.contrib import admin

from .models import *


class SyncSessionAdmin(admin.ModelAdmin):
    list_display = ("get_client_nonce", "client_device", "ip", "server_device", "verified", "closed", "timestamp", "client_version",)
    list_filter = ("verified", "closed", "client_version",)
    
    def get_client_nonce(self, obj):
        return obj.client_nonce[0:5]
    get_client_nonce.short_description = "Client nonce"
admin.site.register(SyncSession, SyncSessionAdmin)


class ImportPurgatoryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "counter", "retry_attempts",)
admin.site.register(ImportPurgatory, ImportPurgatoryAdmin)
