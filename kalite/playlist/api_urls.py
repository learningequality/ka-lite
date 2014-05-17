from django.conf.urls.defaults import include, patterns, url

from .api_resources import PlaylistResource


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^assign/group/(?P<group_id>\w+)/playlist/(?P<playlist_id>\w+)/$', 'assign_group_to_playlist', {}, 'assign_group_to_playlist'),

    # For playlist management
    url(r'^', include(PlaylistResource().urls))
)
