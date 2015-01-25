from django.conf import settings
from django.conf.urls import include, patterns, url

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^teacher/$', 'add_facility_teacher', {},'add_facility_teacher'),
    url(r'^student/$', 'add_facility_student', {}, 'add_facility_student'),
    url(r'^signup/$', 'facility_user_signup', {}, 'facility_user_signup'),
    url(r'^user/(?P<facility_user_id>\w+)/edit/$', 'edit_facility_user', {}, 'edit_facility_user'),

    url(r'^zone/(?P<zone_id>\w+)/facility/new/$', 'facility_edit', {"id": "new"}, 'add_facility'),
    url(r'^facility/(?P<id>\w+)/edit/$', 'facility_edit', {}, 'facility_edit'),

    url(r'^group/$', 'group_edit', {'group_id': 'new'}, 'add_group'),
    url(r'^group/(?P<group_id>\w+)/edit/$', 'group_edit', {'facility': None}, 'group_edit'),

   
)

if not settings.CENTRAL_SERVER:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^login/$', 'login', {}, 'login'),
        url(r'^logout/$', 'logout', {}, 'logout'),
    )

urlpatterns += patterns(__package__ + '.api_views',
    url(r'^api/', include(api_urls)),
)
