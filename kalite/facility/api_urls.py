from django.conf.urls.defaults import patterns, url


# Note that these patterns are all under /api/,
# due to the way they've been included into main/urls.py
urlpatterns = patterns('facility.api_views',
    # For user management
    url(r'^remove_from_group$', 'remove_from_group', {}, 'remove_from_group'),
    url(r'^move_to_group$', 'move_to_group', {}, 'move_to_group'),
    url(r'^delete_users$', 'delete_users', {}, 'delete_users'),
)

