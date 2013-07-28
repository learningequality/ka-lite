from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('central.api_views',
    url(r'^version$', 'get_kalite_version', {}, 'get_kalite_version'),
    url(r'^download/kalite/$', 'get_download_urls', {}, 'get_download_urls'),

    # Only expose publicly available endpoints.  Private ones must be done 
    #   through a secure redirect.
    url(r'^download/kalite/(?P<version>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
)