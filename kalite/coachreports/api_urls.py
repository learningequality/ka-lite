from django.conf.urls import patterns, url, include

from .api_resources import PlaylistProgressResource, PlaylistProgressDetailResource


urlpatterns = patterns(__package__ + '.api_views',
    # Non tasty API
    url(r'data/$',      'api_data', {}, 'api_data'),
    url(r'^data/(?P<xaxis>\w+)/(?P<yaxis>\w+)/$', 'api_data', {}, 'api_data_2'),
    # url(r'friendly/$',  'api_friendly_names', {}, 'api_friendly_names'),
    url(r'^get_topic_tree(?P<topic_path>.*)$', 'get_topic_tree_by_kinds', {}, 'get_topic_tree_by_kinds'),

    # TastyPie API Urls
    url(r'^', include(PlaylistProgressResource().urls)),
    url(r'^', include(PlaylistProgressDetailResource().urls)),
)