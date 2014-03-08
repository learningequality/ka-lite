from django.conf.urls.defaults import include, patterns, url

import api_urls


urlpatterns = patterns('securesync.engine.views',
    url(r'^api/', include(api_urls)),
)
