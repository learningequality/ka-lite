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

from . import api_urls
import kalite.coachreports.urls
import kalite.control_panel.urls
import kalite.facility.urls
import kalite.updates.urls
import securesync.urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/.*$', lambda request: HttpResponseRedirect(settings.STATIC_URL[:-1] + request.path)),
    url(r'^favico.ico/?$', lambda request: HttpResponseRedirect(settings.STATIC_URL + "images/distributed/" + request.path)),
)

urlpatterns += patterns('',
    url(r'^securesync/', include(kalite.facility.urls)),  # for backwards compat
    url(r'^securesync/', include(securesync.urls)),
)

urlpatterns += patterns('',
    url(r'^%s(?P<path>.*)$' % settings.CONTENT_URL[1:], 'django.views.static.serve', {
        'document_root': settings.CONTENT_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
)

# Teaching / admin patterns
urlpatterns += patterns(__package__ + '.views',
    # For teachers
    url(r'^coachreports/', include(kalite.coachreports.urls)),

    # For admins
    url(r'^update/', include(kalite.updates.urls)),

    url(r'^help/$', 'help', {}, 'help'),

    # API
    url(r'^api/', include(api_urls)),

    # Management: Zone, facility, device
    url(r'^management/zone/$', 'zone_redirect', {}, 'zone_redirect'), # only one zone, so make an easy way to access it
    url(r'^management/device/$', 'device_redirect', {}, 'device_redirect'), # only one device, so make an easy way to access it
    url(r'^management/', include(kalite.control_panel.urls)), # no org_id, but parameter needed for reverse url look-up
)

# Testing
if "tests.loadtesting" in settings.INSTALLED_APPS:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^loadtesting/', include('kalite.testing.loadtesting.urls')),
    )

# Front-end
urlpatterns += patterns(__package__ + '.views',
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^watch/$', 'watch_home', {}, 'watch_home'),
    url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
    url(r'^search/$', 'search', {}, 'search'),
    # the following pattern is a catch-all, so keep it last:
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),

    # Allows remote admin of the distributed server
    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),
)

handler403 = __package__ + '.views.handler_403'
handler404 = __package__ + '.views.handler_404'
handler500 = __package__ + '.views.handler_500'
