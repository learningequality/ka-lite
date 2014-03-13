"""
URLs added here should be absolute URLs, as they must be inserted at the highest level
(i.e. central.urls) to guarantee to intercept the request before the appropriate app
or url conf gets called.
"""
from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('stats.api_views',
    url(r'^media/language_packs/(?P<version>.*)/(?P<lang_code>.*).zip$', 'download_language_pack'),
    url(r'^download/videos/(?P<video_path>.*)$', 'download_video'),

    url(r'^download/installer/windows/$', 'download_windows_installer'),
    url(r'^download/installer/windows/(?P<version>.*)$', 'download_windows_installer'),

    url(r'^static/srt/(?P<lang_code>.*)/subtitles/(?P<youtube_id>.*).srt$', 'download_subtitle', {}), # v0.10.0: fetching subtitles.
)
