from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('control_panel.views',
    # Zone
    url(r'zone/(?P<zone_id>\w+)/$', 'zone_management', {}, 'zone_management'),
    url(r'zone/(?P<zone_id>\w+)/edit$', 'zone_form', {}, 'zone_form'),
    url(r'zone/(?P<zone_id>\w+)/upload/$', 'zone_data_upload', {}, 'zone_data_upload'),
    url(r'zone/(?P<zone_id>\w+)/download/$', 'zone_data_download', {}, 'zone_data_download'),

    # Device
    url(r'zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/$', 'device_management', {}, 'device_management'),
    url(r'zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/upload/$', 'device_data_upload', {}, 'device_data_upload'),
    url(r'zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/download/$', 'device_data_download', {}, 'device_data_download'),

    # Facility
    url(r'zone/(?P<zone_id>\w+)/facility/$', 'facility_management', {}, 'facility_management'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/edit$', 'facility_form', {}, 'facility_form'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/users/manage/$', 'facility_user_management', {}, 'facility_user_management'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/mastery/$', 'facility_mastery', {}, 'facility_mastery'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/usage/$', 'facility_usage', {}, 'facility_usage'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/upload/$', 'facility_data_upload', {}, 'facility_data_upload'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/download/$', 'facility_data_download', {}, 'facility_data_download'),

    # Group
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/group/(?P<group_id>\w+)$', 'group_report', {}, 'group_report'),
)