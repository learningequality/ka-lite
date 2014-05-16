from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^sample', 'sample_json'),
    url(r'^assign/group/(?P<group_id>\w+)/playlist/(?P<playlist_id>\w+)/$', 'assign_group_to_playlist', {}, 'assign_group_to_playlist'),
)
