"""
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^update/distributed/$', 'update_all_distributed', {}, 'update_all_distributed'),
    url(r'^update/distributed_callback/$', 'update_all_distributed_callback', {}, 'update_all_distributed_callback'),
)