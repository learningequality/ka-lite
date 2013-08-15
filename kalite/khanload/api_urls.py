from django.conf.urls.defaults import patterns, include, url

import settings


#if settings.CENTRAL_SERVER:
urlpatterns = patterns('khanload.api_views',
    # Distributed server urls
    # Central server urls
    url(r'^update/central/$', 'update_all_central', {}, 'update_all_central'),
    url(r'^oauth/$', 'update_all_central_callback', {}, 'update_all_central_callback'),
)
#else:
urlpatterns += patterns('khanload.api_views',
    url(r'^update/distributed/$', 'update_all_distributed', {}, 'update_all_distributed'),
    url(r'^update/distributed_callback/$', 'update_all_distributed_callback', {}, 'update_all_distributed_callback'),
)