from django.contrib import admin
from models import Deployment

class DeploymentAdmin(admin.ModelAdmin):
    list_display = ('title',)

admin.site.register(Deployment, DeploymentAdmin)
