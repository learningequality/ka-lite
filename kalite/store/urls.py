from django.conf.urls import patterns, url

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^$', 'store', {},'store'),
)
