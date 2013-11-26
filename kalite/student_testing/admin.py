from django.contrib import admin

from models import *

class TestAdmin(admin.ModelAdmin):
    list_display = ("path", "repeats", "seed", "title", "id",)
admin.site.register(Test, TestAdmin)