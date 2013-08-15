from django.conf.urls.defaults import patterns, url, include

import updates.api_urls

urlpatterns = patterns('updates.views',

    url(r'^$', 'update', {}, 'update'),
    url(r'^videos/$', 'update_videos', {}, 'update_videos'),
    url(r'^subtitles/$', 'update_subtitles', {}, 'update_subtitles'),
    url(r'^software/$', 'update_software', {}, 'update_software'),

)