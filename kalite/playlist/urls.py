from django.conf.urls import patterns, url
from django.conf import settings


#Else block url patterns can't be empty because we have a reverse match for assign_playlist/view_playlist

if "nalanda" in settings.CONFIG_PACKAGE:
    urlpatterns = patterns(__package__ + '.views',
                           url(r'^assign/$', 'assign_playlists', {}, 'assign_playlists'),
                           url(r'^view/(?P<playlist_id>\w+)/$', 'view_playlist', {}, 'view_playlist'),
    )
else:
	urlpatterns = patterns(__package__ + '.views',
                           url(r'^/$', 'assign_playlists', {}, 'assign_playlists'),
                           url(r'^/$', 'view_playlist', {}, 'view_playlist'),
    )
