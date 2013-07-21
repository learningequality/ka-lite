from django.conf.urls.defaults import patterns, include, url

urlpatterns += patterns('central.api_views',
    url(r'^get_subtitle_counts/$', 'get_subtitle_counts', {}, 'get_subtitle_counts'),
    url(r'^download/subtitles/(?P<locale>\w+)$', 'download_subtitle_zip', {}, 'download_subtitle_zip'),
)