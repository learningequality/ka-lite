from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

import coachreports.urls
import control_panel.urls
import facility.urls
import khanload.api_urls
import main.api_urls
import securesync.urls
import settings
import updates.urls


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/.*$', lambda request: HttpResponseRedirect(settings.STATIC_URL[:-1] + request.path)),
    url(r'^favico.ico/?$', lambda request: HttpResponseRedirect(settings.STATIC_URL + "images" + request.path)),
    url(r'^securesync/', include(facility.urls)),  # for backwards compat
    url(r'^securesync/', include(securesync.urls)),
)

#i18n
urlpatterns += patterns('',
    url(r'^js/i18n/$', 'main.views.javascript_catalog_cached', {}, 'javascript_catalog_cached'),
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
urlpatterns += patterns('main.views',
    # For teachers
    url(r'^coachreports/', include(coachreports.urls)),

    # For admins
    url(r'^update/', include(updates.urls)),

    url(r'^easyadmin/$', 'easy_admin', {}, 'easy_admin'),

    # API
    url(r'^api/', include(main.api_urls)),
    url(r'^api/khanload/', include(khanload.api_urls)),

    # Management: Zone, facility, device
    url(r'^management/zone/$', 'zone_redirect', {}, 'zone_redirect'), # only one zone, so make an easy way to access it
    url(r'^management/device/$', 'device_redirect', {}, 'device_redirect'), # only one device, so make an easy way to access it
    url(r'^management/', include(control_panel.urls), {"org_id": ""}), # no org_id, but parameter needed for reverse url look-up
)

# Testing
if "tests.loadtesting" in settings.INSTALLED_APPS:
    urlpatterns += patterns('main.views',
        url(r'^loadtesting/', include('tests.loadtesting.urls')),
    )

# Front-end
urlpatterns += patterns('main.views',
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
    url(r'^search/$', 'search', {}, 'search'),
    # the following pattern is a catch-all, so keep it last:
    url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
)

handler403 = 'main.views.handler_403'
handler404 = 'main.views.handler_404'
handler500 = 'main.views.handler_500'
