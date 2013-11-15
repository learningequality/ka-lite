from django.contrib import admin

from models import *

class LanguagePackAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "phrases", "approved_translations", "percent_translated", "language_pack_version", "software_version", "subtitle_count",)
    list_filter = ("code", "name", "phrases", "approved_translations", "percent_translated", "language_pack_version", "software_version", "subtitle_count",)
admin.site.register(LanguagePack, LanguagePackAdmin)
