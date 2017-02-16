"""
"""
from django.conf import settings
from django.conf.urls import include, patterns, url


urlpatterns = patterns('securesync.views',
    url(r'^', include('securesync.devices.urls')),
    url(r'^', include('securesync.engine.urls')),
)
