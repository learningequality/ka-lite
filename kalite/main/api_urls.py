"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls import include, patterns, url

from .api_resources import VideoLogResource, ExerciseLogResource, AttemptLogResource, ContentLogResource,\
    ContentRatingResource


urlpatterns = patterns(__package__ + '.api_views',

    url(r'^', include(VideoLogResource().urls)),
    url(r'^', include(ExerciseLogResource().urls)),
    url(r'^', include(AttemptLogResource().urls)),
    url(r'^', include(ContentLogResource().urls)),
    url(r'^', include(ContentRatingResource().urls)),

    url(r'^assessment_item/(?P<assessment_item_id>.*)/$', 'assessment_item', {}, 'assessment_item'),
    url(r'^content_recommender/?$', 'content_recommender', {}, 'content_recommender'),

    # A flat data structure for building a graphical knowledge map
    url(r'^topic_tree/(?P<channel>.*)/?$', 'topic_tree', {}, 'topic_tree'),

    # An endpoint for querying any fully fleshed out content item.
    url(r'^content/(?P<channel>\w+)/(?P<content_id>[^\s\/]+)/?$', 'content_item', {}, 'content_item'),

    # A search API endpoint
    url(r'^search/(?P<channel>\w+)/$', 'search_api', {}, 'search_api'),

)
