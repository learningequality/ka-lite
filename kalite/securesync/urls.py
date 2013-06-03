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
    url(r'^api/models/download$', 'model_download', {}, 'model_download'),
    url(r'^api/models/upload$', 'model_upload', {}, 'model_upload'),
    url(r'^api/status$', 'status', {}, 'status'),
)

urlpatterns += patterns('securesync.views',
    url(r'^register/$', 'register_public_key', {}, 'register_public_key'),
    url(r'^addteacher/$', 'add_facility_teacher', {}, 'add_facility_teacher'),
    url(r'^addstudent/$', 'add_facility_student', {}, 'add_facility_student'),
    url(r'^facility/$', 'facility_admin', {}, 'facility_admin'),
    url(r'^facility/new/$', 'facility_edit', {"id": "new"}, 'add_facility'),
    url(r'^facility/(?P<id>\w+)/$', 'facility_edit', {}, 'facility_edit'),
    url(r'^addgroup/$', 'add_group', {}, 'add_group'),
    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),
    url(r'^login/$', 'login', {}, 'login'),
    url(r'^logout/$', 'logout', {}, 'logout'),
)
