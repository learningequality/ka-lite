from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from postmark.models import EmailMessage, EmailBounce

class EmailBounceAdmin(admin.ModelAdmin):
    list_display = ("get_message_to", "get_message_to_type", "get_message_subject", "get_message_tag", "type", "bounced_at")
    list_filter = ("type", "message__tag", "bounced_at")
    search_fields = ("message__message_id", "message__subject", "message__to")
    list_select_related = True
    
    readonly_fields = ("id", "message", "inactive", "can_activate", "type", "description", "details", "bounced_at")
    
    def get_message_to(self, obj):
        return u"%s" % obj.message.to
    get_message_to.short_description = _("To")
    
    def get_message_to_type(self, obj):
        return u"%s" % obj.message.get_to_type_display()
    get_message_to_type.short_description = _("Type")
    
    def get_message_subject(self, obj):
        return u"%s" % obj.message.subject
    get_message_subject.short_description = _("Subject")
    
    def get_message_tag(self, obj):
        return u"%s" % obj.message.tag
    get_message_tag.short_description = _("Tag")


class EmailBounceInline(admin.TabularInline):
    model = EmailBounce
    can_delete = False
    
    max_num = 1
    extra = 0
    
    readonly_fields = ("id", "message", "inactive", "can_activate", "type", "description", "details", "bounced_at")


class EmailMessageAdmin(admin.ModelAdmin):
    list_display = ("to", "to_type", "subject", "tag", "status", "submitted_at")
    list_filter = ("status", "tag", "to_type", "submitted_at")
    search_fields = ("message_id", "to", "subject")
    list_select_related = True
    
    readonly_fields = ("message_id", "status", "subject", "tag", "to", "to_type", "sender", "reply_to", "submitted_at", "text_body", "html_body", "headers", "attachments")
    
    inlines = [EmailBounceInline]
    
    fieldsets = (
        (None, {
            "fields": ("message_id", "status", "subject", "tag", "to", "to_type", "sender", "reply_to", "submitted_at")
        }),
        (_("Text Body"), {
            "fields": ("text_body",),
            "classes": ("collapse", "closed")
        }),
        (_("HTML Body"), {
            "fields": ("html_body",),
            "classes": ("collapse", "closed")
        }),
        (_("Advanced"), {
            "fields": ("headers", "attachments"),
            "classes": ("collapse", "closed")
        })
    )

admin.site.register(EmailMessage, EmailMessageAdmin)
admin.site.register(EmailBounce, EmailBounceAdmin)