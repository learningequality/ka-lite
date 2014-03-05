"""
"""
from django.conf.urls.defaults import include, patterns, url


# Note that these patterns are all under /api/,
# due to the way they've been included into main/urls.py
urlpatterns = patterns('main.api_views',

    # For video / exercise pages
    url(r'^save_video_log$', 'save_video_log', {}, 'save_video_log'),
    url(r'^save_exercise_log$', 'save_exercise_log', {}, 'save_exercise_log'),

    # For topic pages with exercise/video leaves
    url(r'^get_video_logs$', 'get_video_logs', {}, 'get_video_logs'),
    url(r'^get_exercise_logs$', 'get_exercise_logs', {}, 'get_exercise_logs'),

    # data used by the frontend search code
    url(r'^flat_topic_tree/(?P<lang_code>.*)/?$', 'flat_topic_tree', {}, 'flat_topic_tree'),

    # For knowledge map
    url(r'^knowledge_map/(?P<topic_id>.*)/?$', 'knowledge_map_json', {}, 'knowledge_map_json'),
)
