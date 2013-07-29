from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponse

import updates.api_urls

# Note that these patterns are all under /api/, 
# due to the way they've been included into main/urls.py
urlpatterns = patterns('main.api_views',

    # toss out any requests made to actual KA site urls
    url(r'^v1/', lambda x: HttpResponse("{}")),

    # For video / exercise pages
    url(r'^save_video_log$', 'save_video_log', {}, 'save_video_log'),
    url(r'^save_exercise_log$', 'save_exercise_log', {}, 'save_exercise_log'),

    # For topic pages with exercise/video leaves
    url(r'^get_video_logs$', 'get_video_logs', {}, 'get_video_logs'),
    url(r'^get_exercise_logs$', 'get_exercise_logs', {}, 'get_exercise_logs'),

    # For update page
    url(r'^start_video_download$', 'start_video_download', {}, 'start_video_download'),
    url(r'^get_topic_tree$', 'get_topic_tree', {}, 'get_topic_tree'),
    url(r'^start_subtitle_download$', 'start_subtitle_download', {}, 'start_subtitle_download'),
    url(r'^check_subtitle_download$', 'check_subtitle_download', {}, 'check_subtitle_download'),
    url(r'^get_subtitle_download_list$', 'get_subtitle_download_list', {}, 'get_subtitle_download_list'),
    url(r'^cancel_downloads$', 'cancel_downloads', {}, 'cancel_downloads'),
    url(r'^delete_videos$', 'delete_videos', {}, 'delete_videos'),

    # For user management
    url(r'^remove_from_group$', 'remove_from_group', {}, 'remove_from_group'),
    url(r'^move_to_group$', 'move_to_group', {}, 'move_to_group'),
    url(r'^delete_users$', 'delete_users', {}, 'delete_users'),

    # For update progress tracking
    url(r'^updates/', include(updates.api_urls)),
)
