from django.conf.urls.defaults import patterns, include, url

import coachreports.api_urls
import khanload.api_urls


urlpatterns = patterns('central.api_views',
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}, 'get_subtitle_counts'),
    url(r'^khanload/', include(khanload.api_urls)),
)
urlpatterns = patterns('coachreports.api_views',
    url(r'^coachreports/', include(coachreports.api_urls)),
)