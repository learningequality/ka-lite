from django.conf.urls import include, patterns, url

from .api_resources import PlaylistResource, QuizLogResource


urlpatterns = patterns(__package__ + '.api_views',
    # For playlist management
    url(r'^', include(PlaylistResource().urls)),	
    # For QuizLogs in playlists
    url(r'^', include(QuizLogResource().urls)),
)
