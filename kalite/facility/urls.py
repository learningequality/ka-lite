from django.conf.urls.defaults import include, patterns, url

from . import api_urls


urlpatterns = patterns('facility.views',
    url(r'^add/teacher/$', 'add_facility_teacher', {},'add_facility_teacher'),
    url(r'^add/student/$', 'add_facility_student', {}, 'add_facility_student'),
    url(r'^edit/(?P<id>\w+)/$', 'edit_facility_user', {}, 'edit_facility_user'),

    url(r'^facility/$', 'facility_admin', {}, 'facility_admin'),
    url(r'^facility/new/$', 'facility_edit', {"id": "new"}, 'add_facility'),
    url(r'^facility/(?P<id>\w+)/$', 'facility_edit', {}, 'facility_edit'),

    url(r'^addgroup/$', 'add_group', {}, 'add_group'),
    url(r'^userlist/$', 'user_list', {}, 'user_list'),

    url(r'^login/$', 'login', {}, 'login'),
    url(r'^logout/$', 'logout', {}, 'logout'),
    url(r'^api/', include(api_urls)),
)
