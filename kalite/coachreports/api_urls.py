from django.conf.urls import patterns, url, include

from .api_resources import PlaylistProgressResource, PlaylistProgressDetailResource


urlpatterns = patterns(__package__ + '.api_views',
    # Non tasty API
    url(r'data/$',      'api_data', {}, 'api_data'),
    url(r'^data/(?P<xaxis>\w+)/(?P<yaxis>\w+)/$', 'api_data', {}, 'api_data_2'),
    # url(r'friendly/$',  'api_friendly_names', {}, 'api_friendly_names'),

    # TastyPie API Urls
    url(r'^', include(PlaylistProgressResource().urls)),
    url(r'^', include(PlaylistProgressDetailResource().urls)),
)