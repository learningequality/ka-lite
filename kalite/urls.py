from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import api.urls

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^api/', include(api.urls)),
    
    url(r'^exercisedashboard/$', 'main.views.exercise_dashboard'),

    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),

    url(r'^(?P<splat>.+)/$', 'main.views.splat_handler'),

)
