"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf.urls.defaults import include, patterns, url


urlpatterns = patterns('main.api_views',

    # For video / exercise pages
    url(r'^save_video_log$', 'save_video_log', {}, 'save_video_log'),
    url(r'^save_exercise_log$', 'save_exercise_log', {}, 'save_exercise_log'),

    # For returning video / exercise progress for a given level within the topic tree
    url(r'^get_video_logs$', 'get_video_logs', {}, 'get_video_logs'),
    url(r'^get_exercise_logs$', 'get_exercise_logs', {}, 'get_exercise_logs'),

    # Data used by the client (browser) for doing search
    url(r'^flat_topic_tree/(?P<lang_code>.*)/?$', 'flat_topic_tree', {}, 'flat_topic_tree'),

    # For building a graphical knowledge map
    url(r'^knowledge_map/(?P<topic_id>.*)/?$', 'knowledge_map_json', {}, 'knowledge_map_json'),
)
