from django.contrib import admin

from .models import *


# class TestAdmin(admin.ModelAdmin):
#     list_display = ("repeats", "seed", "title", "id",)
# admin.site.register(Test, TestAdmin)


class TestLogAdmin(admin.ModelAdmin):
    list_display = ("user", "index", "complete",)
admin.site.register(TestLog, TestLogAdmin)