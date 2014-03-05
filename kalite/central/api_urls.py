from django.conf.urls.defaults import patterns, include, url

import coachreports.api_urls
import i18n.api_urls
import khanload.api_urls


urlpatterns = patterns('central.api_views',
    url(r'^version$', 'get_kalite_version', {}, 'get_kalite_version'),
    url(r'^download/kalite/$', 'get_download_urls', {}, 'get_download_urls'),

    url(r'^khanload/', include(khanload.api_urls)),
)
urlpatterns += patterns('coachreports.api_views',
    url(r'^coachreports/', include(coachreports.api_urls)),
)
urlpatterns += patterns('i18n.api_views',
    url(r'^i18n/', include(i18n.api_urls)),
)
