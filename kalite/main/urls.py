from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import securesync.urls
from kalite import settings


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/(.+)$', lambda request, path: HttpResponseRedirect('/static/images/' + path)),
    url(r'^securesync/', include(securesync.urls)),
)

urlpatterns += patterns('',
    url(r'^%s(?P<path>.*)$' % settings.CONTENT_URL[1:], 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'django.views.static.serve', {
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
)

if getattr(settings, "AUTO_LOAD_TEST", None):
    urlpatterns += patterns('main.views',
        url(r'^loadtesting/', include('loadtesting.urls')),
    )
    
urlpatterns += patterns('main.views',
    # the following pattern is a catch-all, so keep it last:
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
)

handler404 = 'main.views.distributed_404_handler'
handler500 = 'main.views.distributed_500_handler'
