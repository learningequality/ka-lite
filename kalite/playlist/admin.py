from django.contrib import admin

from models import *

class QuizLogAdmin(admin.ModelAdmin):
    list_display = ("user", "index", "complete",)
admin.site.register(QuizLog, QuizLogAdmin)


class PlaylistAdmin(admin.ModelAdmin):
    pass
    # list_display = ("user", "password",)
admin.site.register(Playlist, PlaylistAdmin)


class PlaylistEntryAdmin(admin.ModelAdmin):
    pass
    # list_display = ("user", "password",)
admin.site.register(PlaylistEntry, PlaylistEntryAdmin)


class PlaylistToGroupMappingAdmin(admin.ModelAdmin):
    pass
    list_display = ("playlist", "group",)
admin.site.register(PlaylistToGroupMapping, PlaylistToGroupMappingAdmin)