"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(__package__ + '.api_views',
    # Show pid for the running server (used bt stop to help kill the server)
    url(r'^getpid$', 'getpid', {}, 'getpid'),
)
