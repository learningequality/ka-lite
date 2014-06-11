from django.conf.urls import include, patterns, url

from . import api_urls


urlpatterns = patterns('securesync.devices.views',
    url(r'^register/$', 'register_public_key', {}, 'register_public_key'),
    url(r'^api/', include(api_urls)),
)
