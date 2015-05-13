from django.conf.urls import patterns, url, include

from .api_resources import PlaylistProgressResource, PlaylistProgressDetailResource


urlpatterns = patterns(__package__ + '.api_views',
    url(r'logs/$',      'learner_logs', {}, 'learner_logs'),

    # TastyPie API Urls
    url(r'^', include(PlaylistProgressResource().urls)),
    url(r'^', include(PlaylistProgressDetailResource().urls)),
)