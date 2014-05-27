from django.conf.urls.defaults import include, patterns, url

from .api_resources import PlaylistResource


urlpatterns = patterns(__package__ + '.api_views',
    # For playlist management
    url(r'^', include(PlaylistResource().urls))
)
