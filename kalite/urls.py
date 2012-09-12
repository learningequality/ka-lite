from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import api.urls

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^api/', include(api.urls)),
    
    url(r'^exercisedashboard(?P<splat>.*)/$', 'main.views.exercise_dashboard'),
    # url(r'^exercises/khan-site\.html$', 'main.views.exercise_skeleton'),

    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),
    # url(r'^khan-exercises/(.+)$', lambda request, path: HttpResponseRedirect('/static/khan-exercises/' + path)),
    # url(r'^utils/(.+)$', lambda request, path: HttpResponseRedirect('/static/utils/' + path)),
    # url(r'^css/(.+)$', lambda request, path: HttpResponseRedirect('/static/css/' + path)),
    
    # url(r'^static/khan-exercise.js$', lambda request: HttpResponseRedirect('/static/js/khan-exercise.js')),

    url(r'^(?P<splat>.+)/$', 'main.views.splat_handler'),

)
