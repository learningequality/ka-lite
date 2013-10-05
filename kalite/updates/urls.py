from django.conf.urls.defaults import patterns, url, include

import updates.api_urls

urlpatterns = patterns('updates.views',

    url(r'^$', 'update', {}, 'update'),
    url(r'^videos/$', 'update_videos', {}, 'update_videos'),
    url(r'^languages/$', 'update_languages', {}, 'update_languages'),
    url(r'^software/$', 'update_software', {}, 'update_software'),

)