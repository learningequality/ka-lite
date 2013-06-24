from django.contrib import admin

from models import *


class ContactAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contact, ContactAdmin)

class DeploymentAdmin(admin.ModelAdmin):
    pass
admin.site.register(Deployment, DeploymentAdmin)

class SupportAdmin(admin.ModelAdmin):
    pass
admin.site.register(Support, SupportAdmin)

class InfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Info, InfoAdmin)

class ContributeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contribute, ContributeAdmin)
