from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('updates.api_views',
    url(r'^videos/topic_tree$', 'get_annotated_topic_tree', {}, 'get_annotated_topic_tree'),
    url(r'^videos/start$', 'start_video_download', {}, 'start_video_download'),
    url(r'^videos/delete$', 'delete_videos', {}, 'delete_videos'),
    url(r'^videos/cancel$', 'cancel_video_download', {}, 'cancel_video_download'),
    url(r'^videos/retry$', 'retry_video_download', {}, 'retry_video_download'),

    url(r'^subtitles/start$', 'start_subtitle_download', {}, 'start_subtitle_download'),
    url(r'^subtitles/check$', 'check_subtitle_download', {}, 'check_subtitle_download'),
    url(r'^subtitles/cancel$', 'cancel_subtitle_download', {}, 'cancel_subtitle_download'),

    url(r'^updates/progress$', 'check_update_progress', {}, 'check_update_progress'),
    url(r'^updates/cancel$', 'cancel_update_progress', {}, 'cancel_update_progress'),
    url(r'^updates/start$', 'start_update_kalite', {}, 'start_update_kalite'),
    url(r'^updates/check$', 'check_update_kalite', {}, 'check_update_kalite'),
)