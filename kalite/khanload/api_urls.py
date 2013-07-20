from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('khanload.api_views',
    url(r'^oauth/$', 'update_all_callback', {}, 'update_all_callback'),
    url(r'^update/$', 'update_all', {}, 'update_all'),
)