from django.db import models

from fle_utils.django_utils.classes import ExtendedModel


class FeedListing(ExtendedModel):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    posted_date = models.DateTimeField()
    url = models.URLField()

    def get_absolute_url(self):
        return self.url

class Subscription(ExtendedModel):
    email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, blank=True)

