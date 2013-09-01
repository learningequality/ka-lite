from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponseRedirect

from utils.videos import OUTSIDE_DOWNLOAD_BASE_URL

urlpatterns = patterns('central.api_views',
    url(r'^subtitles/counts/$', 'get_subtitle_counts', {}, 'get_subtitle_counts'),

    url(r'^videos/(.*)$', lambda request, vpath: HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + vpath)),
)