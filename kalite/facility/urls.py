from django.conf.urls.defaults import include, patterns, url

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^add/teacher/$', 'add_facility_teacher', {},'add_facility_teacher'),
    url(r'^add/student/$', 'add_facility_student', {}, 'add_facility_student'),
    url(r'^edit/(?P<id>\w+)/$', 'edit_facility_user', {}, 'edit_facility_user'),

    url(r'^/zone/(?P<zone_id>\w+)/facility/new/$', 'facility_edit', {"id": "new"}, 'facility_edit'),
    url(r'^facility/(?P<id>\w+)/$', 'facility_edit', {}, 'facility_edit'),

    url(r'^addgroup/$', 'add_group', {}, 'add_group'),

    url(r'^login/$', 'login', {}, 'login'),
    url(r'^logout/$', 'logout', {}, 'logout'),
)

urlpatterns += patterns(__package__ + '.api_views',
    url(r'^api/', include(api_urls)),
)
