from django.contrib import admin

from models import *

class QuizLogAdmin(admin.ModelAdmin):
    list_display = ("user", "index", "complete",)
admin.site.register(QuizLog, QuizLogAdmin)