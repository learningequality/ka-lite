from django.conf.urls.defaults import include, patterns, url

import api_urls


urlpatterns = patterns('securesync.devices.views',
    url(r'^register/$', 'register_public_key', {}, 'register_public_key'),
    url(r'^api/', include(api_urls)),
)
