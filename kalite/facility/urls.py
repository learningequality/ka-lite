from django.conf.urls.defaults import include, patterns, url

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^teacher/new/$', 'add_facility_teacher', {},'add_facility_teacher'),
    url(r'^student/new/$', 'add_facility_student', {}, 'add_facility_student'),
    url(r'^user/(?P<id>\w+)/edit/$', 'edit_facility_user', {}, 'edit_facility_user'),

    url(r'^zone/(?P<zone_id>\w+)/facility/new/$', 'facility_edit', {"id": "new"}, 'add_facility'),
    url(r'^facility/(?P<id>\w+)/edit/$', 'facility_edit', {}, 'facility_edit'),

    url(r'^addgroup/$', 'add_group', {}, 'add_group'),

    url(r'^login/$', 'login', {}, 'login'),
    url(r'^logout/$', 'logout', {}, 'logout'),
)

urlpatterns += patterns(__package__ + '.api_views',
    url(r'^api/', include(api_urls)),
)
