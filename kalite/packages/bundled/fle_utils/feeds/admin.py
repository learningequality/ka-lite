from django.contrib import admin

from .models import *


class FeedListingAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "posted_date")
admin.site.register(FeedListing, FeedListingAdmin)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "timestamp", "ip",)
admin.site.register(Subscription, SubscriptionAdmin)