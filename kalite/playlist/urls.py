from django.conf.urls import patterns, url


urlpatterns = patterns(__package__ + '.views',
                       url(r'^assign/$', 'assign_playlists', {}, 'assign_playlists'),
                       url(r'^view/(?P<playlist_id>\w+)/$', 'view_playlist', {}, 'view_playlist'),
)
