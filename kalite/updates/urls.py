from django.conf.urls.defaults import patterns, url, include

import updates.api_urls

urlpatterns = patterns('updates.views',

    url(r'^$', 'update', {}, 'update'),
    url(r'^update/videos/$', 'update_videos', {}, 'update_videos'),
    url(r'^update/subtitles/$', 'update_subtitles', {}, 'update_subtitles'),
    url(r'^update/software/$', 'update_software', {}, 'update_software'),

    url(r'^api/', include(updates.api_urls)),
)

