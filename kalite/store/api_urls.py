"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls import include, patterns, url

from .api_resources import StoreItemResource, StoreTransactionLogResource


urlpatterns = patterns('',
    url(r'^', include(StoreItemResource().urls)),
    url(r'^', include(StoreTransactionLogResource().urls)),
)
