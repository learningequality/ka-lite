"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls import include, patterns, url

from .api_resources import ExerciseLogResource, AttemptLogResource, ContentLogResource, VideoResource, ExerciseResource, AssessmentItemResource, ContentResource


urlpatterns = patterns(__package__ + '.api_views',

    # For video / exercise pages
    url(r'^save_video_log$', 'save_video_log', {}, 'save_video_log'),

    # For returning video / exercise progress for a given level within the topic tree
    url(r'^get_video_logs$', 'get_video_logs', {}, 'get_video_logs'),
    url(r'^get_exercise_logs$', 'get_exercise_logs', {}, 'get_exercise_logs'),
    url(r'^get_content_logs$', 'get_content_logs', {}, 'get_content_logs'),

    url(r'^', include(ExerciseLogResource().urls)),
    url(r'^', include(AttemptLogResource().urls)),
    url(r'^', include(ContentLogResource().urls)),
    # Retrieve video data to render a front-end video player
    url(r'^', include(VideoResource().urls)),
    # Retrieve exercise data to render a front-end exercise
    url(r'^', include(ExerciseResource().urls)),
    # Retrieve assessment item data to render front-end Perseus Exercises
    url(r'^', include(AssessmentItemResource().urls)),
    url(r'^', include(ContentResource().urls)),
    url(r'^exercise_log/(?P<exercise_id>\w+)$', 'exercise_log', {}, 'exercise_log'),
    url(r'^attempt_log/(?P<exercise_id>\w+)$', 'attempt_log', {}, 'attempt_log'),

    # Data used by the client (browser) for doing search
    url(r'^flat_topic_tree/(?P<lang_code>.*)/?$', 'flat_topic_tree', {}, 'flat_topic_tree'),

    # For building a graphical knowledge map
    url(r'^knowledge_map/(?P<topic_id>.*)/?$', 'knowledge_map_json', {}, 'knowledge_map_json'),

)
