from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('stats.api_views',
    url(r'^media/language_packs/(?P<version>.*)/(?P<lang_code>.*).zip$', 'download_language_pack'),
    url(r'^download/videos/(?P<video_path>.*)$', 'download_video'),
)
