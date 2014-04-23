from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(__package__ + '.api_views',
    # For user management
    url(r'^move_to_group$', 'move_to_group', {}, 'move_to_group'),
    url(r'^delete_users$', 'delete_users', {}, 'delete_users'),

    url(r'^facility_delete$', 'facility_delete', {}, 'facility_delete'),
    url(r'^facility_delete/(?P<facility_id>\w+)$', 'facility_delete', {}, 'facility_delete'),
)

