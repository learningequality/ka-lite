from django.conf.urls import include, patterns, url

from . import api_urls


urlpatterns = patterns('securesync.engine.views',
    url(r'^api/', include(api_urls)),
)
