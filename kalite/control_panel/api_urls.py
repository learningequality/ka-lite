from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(__package__ + '.api_views',
    url(r'zone/(?P<zone_id>\w+)/delete$', 'delete_zone', {}, 'delete_zone'),
)