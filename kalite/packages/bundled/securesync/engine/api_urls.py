from django.conf.urls import patterns, url


# Note that these patterns are all under /api/,
# due to the way they've been included into main/urls.py
urlpatterns = patterns('securesync.engine.api_views',
    url(r'^session/create$', 'create_session', {}, 'create_session'),
    url(r'^session/destroy$', 'destroy_session', {}, 'destroy_session'),
    url(r'^device/counters$', 'device_counters', {}, 'device_counters'),
    url(r'^device/download$', 'device_download', {}, 'device_download'),
    url(r'^models/download$', 'model_download', {}, 'model_download'),
    url(r'^models/upload$', 'model_upload', {}, 'model_upload'),

    url(r'^force_sync$', 'force_sync', {}, 'api_force_sync'),
)

