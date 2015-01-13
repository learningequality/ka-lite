from django.conf.urls import patterns, url
from django.conf import settings


if getattr(settings, "CONFIG_PACKAGE", False) == "Nalanda":
    urlpatterns = patterns(__package__ + '.views',
                           url(r'^assign/$', 'assign_playlists', {}, 'assign_playlists'),
                           url(r'^view/(?P<playlist_id>\w+)/$', 'view_playlist', {}, 'view_playlist'),
    )
else:
	urlpatterns = patterns(__package__ + '.views',
                           url(r'^/$', 'assign_playlists', {}, 'assign_playlists'),
                           url(r'^/$', 'view_playlist', {}, 'view_playlist'),
    )
