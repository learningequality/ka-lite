from django.conf.urls import patterns, url


# Note that these patterns are all under /api/,
# due to the way they've been included into main/urls.py
urlpatterns = patterns('securesync.devices.api_views',
    url(r'^register$', 'register_device', {}, 'register_device'),
    url(r'^test$', 'test_connection', {}, 'test_connection'),
    url(r'^info$', 'get_server_info', {}, 'get_server_info'),
)

