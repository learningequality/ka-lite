from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(__package__ + '.views',
    # Zone
    url(r'zone/(?P<zone_id>\w+)/$', 'zone_management', {}, 'zone_management'),
    url(r'zone/(?P<zone_id>\w+)/edit$', 'zone_form', {}, 'zone_form'),
    url(r'zone/(?P<zone_id>\w+)/delete$', 'delete_zone', {}, 'delete_zone'),

    # Device
    url(r'zone/(?P<zone_id>\w+)/device/(?P<device_id>\w+)/$', 'device_management', {}, 'device_management'),

    # Facility
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/edit$', 'facility_form', {}, 'facility_form'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/management/$', 'facility_management', {}, 'facility_management'),
    url(r'zone/(?P<zone_id>\w+)/facility/(?P<facility_id>\w+)/management/group/(?P<group_id>\w+)/$', 'facility_management', {}, 'facility_management'),

    url(r'account/$', 'account_management', {}, 'account_management'),
)