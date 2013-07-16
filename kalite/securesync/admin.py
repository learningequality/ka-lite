from django.contrib import admin
from models import *


class SyncSessionAdmin(admin.ModelAdmin):
    list_display = ("get_client_nonce", "client_device", "ip", "server_device", "verified", "closed", "timestamp", "client_version",)
    list_filter = ("verified", "closed", "client_version",)
    
    def get_client_nonce(self, obj):
        return obj.client_nonce[0:5]
    get_client_nonce.short_description = "Client nonce"
    
admin.site.register(SyncSession, SyncSessionAdmin)


class RegisteredDevicePublicKeyAdmin(admin.ModelAdmin):
    list_display = ("public_key", "zone",)
    list_filter = ("zone",)
admin.site.register(RegisteredDevicePublicKey, RegisteredDevicePublicKeyAdmin)


class DeviceMetadataAdmin(admin.ModelAdmin):
    list_display = ("device", "is_trusted", "is_own_device", "counter_position",)
admin.site.register(DeviceMetadata, DeviceMetadataAdmin)


class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "description",)
admin.site.register(Zone, ZoneAdmin)


class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "address",)
admin.site.register(Facility, FacilityAdmin)


class FacilityGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "facility",)
admin.site.register(FacilityGroup, FacilityGroupAdmin)


class FacilityUserAdmin(admin.ModelAdmin):
    list_display = ("facility", "username", "first_name", "last_name",)
    list_filter = ("facility",)
admin.site.register(FacilityUser, FacilityUserAdmin)


class DeviceZoneAdmin(admin.ModelAdmin):
    list_display = ("device", "zone",)
    list_filter = ("device", "zone",)
admin.site.register(DeviceZone, DeviceZoneAdmin)


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "description", "is_own_device", "is_trusted", "get_zone", "version")
    
    def is_own_device(self, obj):
        return obj.devicemetadata.is_own_device
    is_own_device.boolean = True
    is_own_device.admin_order_field = "devicemetadata__is_own_device"
    
    def is_trusted(self, obj):
        return obj.devicemetadata.is_trusted
    is_trusted.boolean = True
    is_trusted.admin_order_field = "devicemetadata__is_trusted"

    def device_id(self, obj):
        return obj.id[0:5]
    device_id.admin_order_field = "id"

admin.site.register(Device, DeviceAdmin)

class ImportPurgatoryAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "counter", "retry_attempts",)
admin.site.register(ImportPurgatory, ImportPurgatoryAdmin)
