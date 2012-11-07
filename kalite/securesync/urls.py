from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('securesync.api_views',
    url(r'^api/register$', 'register_device', {}, 'register_device'),
    url(r'^api/test$', 'test_connection', {}, 'test_connection'),
    url(r'^api/session/create$', 'create_session', {}, 'create_session'),
    url(r'^api/session/destroy$', 'destroy_session', {}, 'destroy_session'),
    url(r'^api/device/counters$', 'device_counters', {}, 'device_counters'),
    url(r'^api/device/download$', 'device_download', {}, 'device_download'),
    url(r'^api/models/download$', 'download_models', {}, 'download_models'),
    url(r'^api/models/upload$', 'upload_models', {}, 'upload_models'),
    url(r'^api/status$', 'status', {}, 'status'),
)

urlpatterns += patterns('securesync.views',
    url(r'^register/$', 'register_public_key', {}, 'register_public_key'),
    url(r'^adduser/$', 'add_facility_user', {}, 'add_facility_user'),
    url(r'^facility/(?P<id>\w+)/adduser/$', 'add_facility_user_selected', {}, 'add_facility_user_selected'),
    url(r'^addfacility/$', 'add_facility', {}, 'add_facility'),
    url(r'^addgroup/(?P<id>\w+)/$', 'add_group', {}, 'add_group'),
    url(r'^login/$', 'login', {}, 'login'),
    url(r'^logout/$', 'logout', {}, 'logout'),
)
