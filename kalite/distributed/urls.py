"""
URLS for constructing the KA Lite app. Mostly imported from other apps.
Notable urls include:
* serving media and static files.  This can be overriden by putting a (fast) front-end server
    (like nginx) to speed things up.
* The "splat" handler, which catches all uncaught requests, and tries to turn them into a
    node in the topic tree.
"""
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.http import HttpResponseRedirect

import api_urls
import coachreports.urls
import control_panel.urls
import facility.urls
import securesync.urls
import updates.urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/.*$', lambda request: HttpResponseRedirect(settings.STATIC_URL[:-1] + request.path)),
    url(r'^favico.ico/?$', lambda request: HttpResponseRedirect(settings.STATIC_URL + "images" + request.path)),
)

urlpatterns += patterns('',
    url(r'^securesync/', include(facility.urls)),  # for backwards compat
    url(r'^securesync/', include(securesync.urls)),
)

#i18n
urlpatterns += patterns('',
    url(r'^js/i18n/$', 'distributed.views.javascript_catalog_cached', {}, 'javascript_catalog_cached'),
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

# Teaching / admin patterns
urlpatterns += patterns('distributed.views',
    # For teachers
    url(r'^coachreports/', include(coachreports.urls)),

    # For admins
    url(r'^update/', include(updates.urls)),

    url(r'^easyadmin/$', 'easy_admin', {}, 'easy_admin'),
    url(r'^userlist/$', 'user_list', {}, 'user_list'),

    # API
    url(r'^api/', include(api_urls)),
    url(r'^api/khanload/', include(khanload.api_urls)),

    # Management: Zone, facility, device
    url(r'^management/zone/$', 'zone_redirect', {}, 'zone_redirect'), # only one zone, so make an easy way to access it
    url(r'^management/device/$', 'device_redirect', {}, 'device_redirect'), # only one device, so make an easy way to access it
    url(r'^management/', include(control_panel.urls), {"org_id": ""}), # no org_id, but parameter needed for reverse url look-up
)

# Testing
if "tests.loadtesting" in settings.INSTALLED_APPS:
    urlpatterns += patterns('distributed.views',
        url(r'^loadtesting/', include('tests.loadtesting.urls')),
    )

# Front-end
urlpatterns += patterns('distributed.views',
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
    url(r'^search/$', 'search', {}, 'search'),
    # the following pattern is a catch-all, so keep it last:
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),

    # Allows remote admin of the distributed server
    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),
)



handler403 = 'distributed.views.handler_403'
handler404 = 'distributed.views.handler_404'
handler500 = 'distributed.views.handler_500'
