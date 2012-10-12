from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import api.urls
from kalite import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^api/', include(api.urls)),
    
    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),

)

if settings.CENTRAL_SERVER:

    urlpatterns += patterns('',
    
        url(r'^$', 'central.views.homepage_handler'), 
    
    )

else:
    
    urlpatterns += patterns('',
        
        url(r'^exercisedashboard/$', 'main.views.exercise_dashboard'),
        
        url(r'^$', 'main.views.homepage_handler'),
        
        url(r'^videodownload/$', 'main.views.video_download'),
        
        url(r'^(?P<splat>.+)/$', 'main.views.splat_handler'),

    )