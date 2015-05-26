"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls import include, patterns, url

from .api_resources import VideoLogResource, ExerciseLogResource, AttemptLogResource, ContentLogResource, ExerciseResource, AssessmentItemResource, ContentResource


urlpatterns = patterns(__package__ + '.api_views',

    url(r'^', include(VideoLogResource().urls)),
    url(r'^', include(ExerciseLogResource().urls)),
    url(r'^', include(AttemptLogResource().urls)),
    url(r'^', include(ContentLogResource().urls)),
    # Retrieve exercise data to render a front-end exercise
    url(r'^', include(ExerciseResource().urls)),
    # Retrieve assessment item data to render front-end Perseus Exercises
    url(r'^', include(AssessmentItemResource().urls)),
    url(r'^', include(ContentResource().urls)),
    
    url(r'^content_recommender/?$', 'content_recommender', {}, 'content_recommender'),

    # A flat data structure for building a graphical knowledge map
    url(r'^topic_tree/(?P<channel>.*)/?$', 'topic_tree', {}, 'topic_tree'),

)
