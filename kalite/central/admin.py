from django.contrib import admin
from models import *


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "url")
admin.site.register(Organization, OrganizationAdmin)

class UserProfileAdmin(admin.ModelAdmin):
	list_display = ("user",)
admin.site.register(UserProfile, UserProfileAdmin)
