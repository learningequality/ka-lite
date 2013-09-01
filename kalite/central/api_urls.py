from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('central.api_views',
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}, 'get_subtitle_counts'),
)