from django.contrib import admin
from models import *


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "url")
admin.site.register(Organization, OrganizationAdmin)


class ZoneOrganizationAdmin(admin.ModelAdmin):
    list_display = ("zone", "organization",)
    list_filter = ("zone", "organization",)
admin.site.register(ZoneOrganization, ZoneOrganizationAdmin)


# class OrganizationUserAdmin(admin.ModelAdmin):
#     list_display = ("user", "organization",)
#     list_filter = ("user", "organization",)
# admin.site.register(OrganizationUser, OrganizationUserAdmin)
