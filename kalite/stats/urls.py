from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('stats.views',
    url(r'^syncing/$', 'recent_syncing', {}, 'recent_syncing'),
    url(r'^timelines/$', 'timelines', {}, 'timelines'),
)
