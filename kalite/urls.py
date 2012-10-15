from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import securesync.urls
from kalite import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),
    url(r'^securesync/', include(securesync.urls)),
)

if settings.CENTRAL_SERVER:

    urlpatterns += patterns('',
        url(r'^$', 'central.views.homepage', {}, 'homepage'), 
        url(r'^accounts/', include('registration.urls')),
    )

else:
    
    urlpatterns += patterns('main.views',
        url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
        url(r'^$', 'homepage', {}, 'homepage'),
        url(r'^videodownload/$', 'video_download', {}, 'video_download'),
        url(r'^api/', include('main.api_urls')),
        url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
    )