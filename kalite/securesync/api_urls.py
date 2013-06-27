from django.conf.urls.defaults import patterns, url


# Note that these patterns are all under /api/, 
# due to the way they've been included into main/urls.py
urlpatterns = patterns('securesync.api_views',
    url(r'^register$', 'register_device', {}, 'register_device'),
    url(r'^test$', 'test_connection', {}, 'test_connection'),
    url(r'^session/create$', 'create_session', {}, 'create_session'),
    url(r'^session/destroy$', 'destroy_session', {}, 'destroy_session'),
    url(r'^device/counters$', 'device_counters', {}, 'device_counters'),
    url(r'^device/download$', 'device_download', {}, 'device_download'),
    url(r'^models/download$', 'model_download', {}, 'model_download'),
    url(r'^models/upload$', 'model_upload', {}, 'model_upload'),
    url(r'^status$', 'status', {}, 'status'),
)

