"""
"""
from django.conf.urls.defaults import patterns, include, url


urlpatterns = patterns('khanload.api_views',
    url(r'^update/distributed/$', 'update_all_distributed', {}, 'update_all_distributed'),
    url(r'^update/distributed_callback/$', 'update_all_distributed_callback', {}, 'update_all_distributed_callback'),
)