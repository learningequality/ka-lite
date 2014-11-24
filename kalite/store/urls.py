from django.conf import settings
from django.conf.urls import include, patterns, url

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^$', 'store', {},'store'),
)
