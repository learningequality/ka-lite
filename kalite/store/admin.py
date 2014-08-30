from django.contrib import admin

from .models import *


# class StoreItemAdmin(admin.ModelAdmin):
#     list_display = ("title", "cost",)
# admin.site.register(StoreItem, StoreItemAdmin)


class StoreTransactionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "user", "purchased_at")
admin.site.register(StoreTransactionLog, StoreTransactionLogAdmin)
