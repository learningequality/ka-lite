from django.contrib import admin
from models import *


class SyncSessionAdmin(admin.ModelAdmin):
    list_display = ("client_device", "server_device", "verified",)
    list_filter = ("verified",)
admin.site.register(SyncSession, SyncSessionAdmin)


class RegisteredDevicePublicKeyAdmin(admin.ModelAdmin):
    list_display = ("public_key",)
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


class FacilityUserAdmin(admin.ModelAdmin):
    list_display = ("facility", "username", "first_name", "last_name",)
    list_filter = ("facility",)
admin.site.register(FacilityUser, FacilityUserAdmin)


class DeviceZoneAdmin(admin.ModelAdmin):
    list_display = ("device", "zone",)
    list_filter = ("device", "zone",)
admin.site.register(DeviceZone, DeviceZoneAdmin)


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "description",)
admin.site.register(Device, DeviceAdmin)

