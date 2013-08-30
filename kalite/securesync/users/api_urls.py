from django.conf.urls.defaults import patterns, url


# Note that these patterns are all under /api/, 
# due to the way they've been included into main/urls.py
urlpatterns = patterns('securesync.users.api_views',
    url(r'^status$', 'status', {}, 'status'),
)

