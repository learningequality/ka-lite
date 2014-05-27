from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(__package__ + '.views',
                       url(r'^assign/$', 'assign_playlists', {}, 'assign_playlists'),
                       url(r'^view/$', 'view_playlist', {}, 'view_playlist'),
)
