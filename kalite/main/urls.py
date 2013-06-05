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

urlpatterns += patterns('',
    url(r'^' + settings.CONTENT_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
    url(r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_URL,
    }),
    url(r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.STATIC_ROOT,
    }),
)

# Javascript translations
urlpatterns += patterns('',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': ('ka-lite.locale')}, 'i18n_javascript_catalog'),
)

urlpatterns += patterns('main.views',
    url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
    url(r'^coachreports/$', 'coach_reports', {}, 'coach_reports'),
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^update/$', 'update', {}, 'update'),
    url(r'^userlist/$', 'user_list', {}, 'user_list'),
    url(r'^api/', include('main.api_urls')),
    url(r'^loadtesting/', include('loadtesting.urls')),
    
    # the following pattern is a catch-all, so keep it last:
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
)

handler404 = 'main.views.distributed_404_handler'
handler500 = 'main.views.distributed_500_handler'
