from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('control_panel.views',
    # Database-wide; disabling here because otherwise it needs org info :-/
    # url(r'^summary/$', 'admin_summary_page', {}, 'admin_summary_page'),

    # Zone
    url(r'zone/(?P<zone_id>\w+)/$', 'zone_management', {}, 'zone_management'),
    url(r'zone/(?P<zone_id>\w+)/edit$', 'zone_form', {}, 'zone_form'),
    url(r'zone/(?P<zone_id>\w+)/delete$', 'delete_zone', {}, 'delete_zone'),

    # Device
    url(r'zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/$', 'device_management', {}, 'device_management'),

    # Facility
    url(r'zone/(?P<zone_id>\w+)/facility/$', 'facility_management', {}, 'facility_management'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/edit$', 'facility_form', {}, 'facility_form'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/usage/$', 'facility_usage', {}, 'facility_usage'),
#    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/users/manage/$', 'facility_user_management', {}, 'facility_user_management'),

    url(r'account/$', 'account_management', {}, 'account_management'),

    # Group
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/group/(?P<group_id>\w+)/users/manage/$', 'facility_user_management', {}, 'facility_user_management'),
)