from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('updates.api_views',
    url(r'^videos/topic_tree$', 'get_annotated_topic_tree', {}, 'get_annotated_topic_tree'),
    url(r'^videos/start$', 'start_video_download', {}, 'start_video_download'),
    url(r'^videos/delete$', 'delete_videos', {}, 'delete_videos'),
    url(r'^videos/cancel$', 'cancel_video_download', {}, 'cancel_video_download'),
    url(r'^videos/retry$', 'retry_video_download', {}, 'retry_video_download'),

    url(r'^languagepacks/start$', 'start_languagepack_download', {}, 'start_languagepack_download'),
    url(r'^languagepacks/installed$', 'installed_language_packs', {}, 'installed_language_packs'),

    url(r'^software/start$', 'start_update_kalite', {}, 'start_update_kalite'),

    url(r'^updates/progress$', 'check_update_progress', {}, 'check_update_progress'),
    url(r'^updates/cancel$', 'cancel_update_progress', {}, 'cancel_update_progress'),

    url(r'^server/restart$', 'server_restart', {}, 'server_restart'),
)
