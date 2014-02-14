from django.contrib import admin

from .models import *


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


class CachedPasswordAdmin(admin.ModelAdmin):
    list_display = ("user", "password",)
admin.site.register(CachedPassword, CachedPasswordAdmin)