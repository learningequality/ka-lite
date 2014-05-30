from django.conf.urls import patterns, url, include

from .api_resources import FacilityGroupResource, FacilityUserResource


urlpatterns = patterns(__package__ + '.api_views',
    # For user management
    url(r'^move_to_group$', 'move_to_group', {}, 'move_to_group'),
    url(r'^delete_users$', 'delete_users', {}, 'delete_users'),

    url(r'^facility_delete$', 'facility_delete', {}, 'facility_delete'),
    url(r'^facility_delete/(?P<facility_id>\w+)$', 'facility_delete', {}, 'facility_delete'),

    url(r'^group_delete$', 'group_delete', {}, 'group_delete'),
    url(r'^group_delete/(?P<group_id>\w+)$', 'group_delete', {}, 'group_delete'),

    # For group management
    url(r'^', include(FacilityGroupResource().urls)),

    # For user management (not yet used, but needed here to enable URI for tastypie exercise logging endpoints)
    url(r'^', include(FacilityUserResource().urls)),
)
