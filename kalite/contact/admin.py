from django.contrib import admin
from models import Contact, Deployment, Support, Info, Contribute
            
class ContactAdmin(admin.ModelAdmin):
    pass
class DeploymentAdmin(admin.ModelAdmin):
    pass
class SupportAdmin(admin.ModelAdmin):
    pass
class InfoAdmin(admin.ModelAdmin):
    pass
class ContributeAdmin(admin.ModelAdmin):
    pass
    
admin.site.register(Contact, ContactAdmin)
admin.site.register(Deployment, DeploymentAdmin)
admin.site.register(Support, SupportAdmin)
admin.site.register(Info, InfoAdmin)
admin.site.register(Contribute, ContributeAdmin)
