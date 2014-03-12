from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponseServerError

import settings
import updates.api_urls


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

    url(r'^launch_mplayer$', 'launch_mplayer', {}, 'launch_mplayer'),

    url(r'^status$', 'status', {}, 'status'),

    #API endpoint for setting server time
    url(r'^time_set/$', 'time_set', {}, 'time_set'),

    # show pid for the running server (used bt stop to help kill the server)
    url(r'^getpid$', 'getpid', {}, 'getpid'),
)


urlpatterns += patterns('updates.api_views',
    url(r'^', include(updates.api_urls)),
)

# Placed at the bottom, so that it's the last to be checked (not first)
urlpatterns += patterns('',
    # toss out any requests made to actual KA site urls
    url(r'^v1/', lambda x: HttpResponseServerError("This is an assert--you should disable these calls from KA in the javascript code!")),
)
