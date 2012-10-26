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
    list_display = ("device", "is_trusted_authority", "is_own_device", "counter_position",)
admin.site.register(DeviceMetadata, DeviceMetadataAdmin)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "url")
admin.site.register(Organization, OrganizationAdmin)


class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "description",)
admin.site.register(Zone, ZoneAdmin)


class ZoneOrganizationAdmin(admin.ModelAdmin):
    list_display = ("zone", "organization",)
    list_filter = ("zone", "organization",)
admin.site.register(ZoneOrganization, ZoneOrganizationAdmin)


class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ("user", "organization",)
    list_filter = ("user", "organization",)
admin.site.register(OrganizationUser, OrganizationUserAdmin)


class FacilityAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "zone")
    list_filter = ("zone",)
admin.site.register(Facility, FacilityAdmin)


class FacilityUserAdmin(admin.ModelAdmin):
    list_display = ("facility", "username", "first_name", "last_name",)
    list_filter = ("facility",)
admin.site.register(FacilityUser, FacilityUserAdmin)


class DeviceZoneAdmin(admin.ModelAdmin):
    list_display = ("device", "zone", "primary",)
    list_filter = ("device", "zone",)
admin.site.register(DeviceZone, DeviceZoneAdmin)


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "description",)
admin.site.register(Device, DeviceAdmin)

