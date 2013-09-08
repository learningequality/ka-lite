from django.conf.urls.defaults import patterns, include, url

import khanload.api_urls


urlpatterns = patterns('central.api_views',
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}, 'get_subtitle_counts'),
    url(r'^khanload/', include(khanload.api_urls)),
)
