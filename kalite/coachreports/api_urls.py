from django.conf.urls import patterns, url, include


urlpatterns = patterns(__package__ + '.api_views',
    url(r'data/$',      'api_data', {}, 'api_data'),
    url(r'^data/(?P<xaxis>\w+)/(?P<yaxis>\w+)/$', 'api_data', {}, 'api_data_2'),
#    url(r'friendly/$',  'api_friendly_names', {}, 'api_friendly_names'),
    url(r'^get_topic_tree(?P<topic_path>.*)$', 'get_topic_tree_by_kinds', {}, 'get_topic_tree_by_kinds')
)

