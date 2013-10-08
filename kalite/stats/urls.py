from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('stats.views',
    url(r'^summary/$', 'recent_syncing', {}, 'recent_syncing'),
    url(r'^timelines/$', 'timelines', {}, 'timelines'),
)
