from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

import main.api_urls
import central.api_urls
import coachreports.urls
import contact.urls
import control_panel.urls
import faq.urls
import registration.urls
import securesync.urls
import settings
import stats.api_urls, stats.urls
from feeds import RssSiteNewsFeed, AtomSiteNewsFeed
from utils.videos import OUTSIDE_DOWNLOAD_BASE_URL  # for video download redirects


admin.autodiscover()

def redirect_to(self, base_url, path=""):
    return HttpResponseRedirect(base_url + path)

# This must be prioritized, to make sure stats are recorded for all necessary urls.
#   If removed, all apps should still function, as appropriate URL confs for each
#   app still exist
urlpatterns = patterns('stats.api_views',
    url(r'^', include(stats.api_urls)),  # add at root
)


urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^images/.*$', lambda request: HttpResponseRedirect(settings.STATIC_URL[:-1] + request.path)),
    url(r'^securesync/', include(securesync.urls)),
)

urlpatterns += patterns('',
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
    url(r'^%s(?P<path>.*)$' % settings.STATIC_URL[1:], 'django.views.static.serve', {
        'document_root': settings.STATIC_ROOT,
    }),
)

urlpatterns += patterns('central.views',
    url(r'^$', 'homepage', {}, 'homepage'),
    url(r'^content/(?P<page>\w+)/', 'content_page', {}, 'content_page'), # Example of a new landing page
    url(r'^wiki/(?P<path>.*)$', 'content_page', {"page": "wiki_page", "wiki_site": settings.CENTRAL_WIKI_URL}, 'wiki'),

    url(r'^delete_admin/(?P<org_id>\w+)/(?P<user_id>\w+)/$', 'delete_admin', {}, 'delete_admin'),
    url(r'^delete_invite/(?P<org_id>\w+)/(?P<invite_id>\w+)/$', 'delete_invite', {}, 'delete_invite'),
    url(r'^accounts/', include(registration.urls)),

    # Organization
    url(r'^organization/$', 'org_management', {}, 'org_management'),
    url(r'^organization/(?P<org_id>\w+)/$', 'organization_form', {}, 'organization_form'),
    url(r'^organization/invite_action/(?P<invite_id>\w+)/$', 'org_invite_action', {}, 'org_invite_action'),
    url(r'^organization/delete/(?P<org_id>\w+)/$', 'delete_organization', {}, 'delete_organization'),
    url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/delete$', 'delete_zone', {}, 'delete_zone'),

    # Zone, facility, device
    url(r'^organization/(?P<org_id>\w+)/', include(control_panel.urls)),

    # Reporting
    url(r'^coachreports/', include(coachreports.urls)),

    url(r'^glossary/$', 'glossary', {}, 'glossary'),
    url(r'^addsubscription/$', 'add_subscription', {}, 'add_subscription'),
    url(r'^feeds/rss/$', RssSiteNewsFeed(), {}, 'rss_feed'),
    url(r'^feeds/atom/$', AtomSiteNewsFeed(), {}, 'atom_feed'),
    url(r'^faq/', include(faq.urls)),

    # The install wizard app has two views: both options available (here)
    #   or an "edition" selected (to get more info, or redirect to download, below)
    #url(r'^download/wizard/$', 'download_wizard', {}, 'download_wizard'),
    #url(r'^download/wizard/(?P<edition>[\w-]+)/$', 'download_wizard', {}, 'download_wizard'),
    #url(r'^download/thankyou/$', 'download_thankyou', {}, 'download_thankyou'),

    # Downloads: public
    #url(r'^download/kalite/(?P<version>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    #url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    #url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/$', 'download_kalite_public', {}, 'download_kalite_public'),
    # Downloads: private
    #url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/(?P<zone_id>[^\/]+)/$', 'download_kalite_private', {}, 'download_kalite_private'),
    #url(r'^download/kalite/(?P<version>[^\/]+)/(?P<platform>[^\/]+)/(?P<locale>[^\/]+)/(?P<zone_id>[^\/]+)/(?P<include_data>[^\/]+)/$', 'download_kalite_private', {}, 'download_kalite_private'),

    # The following has been superceded by the stats app, but we
    #   keep it here so that things will function even if that app is removed.
    url(r'^download/videos/(.*)$', lambda request, vpath: HttpResponseRedirect(OUTSIDE_DOWNLOAD_BASE_URL + vpath)),

    url(r'^wiki/installation/$', 'content_page', {"page": "wiki_page", "wiki_site": settings.CENTRAL_WIKI_URL, "path": "/installation/"}, 'install'),

    url(r'^contact/', include(contact.urls)),
    url(r'^about/$', lambda request: HttpResponseRedirect('http://learningequality.org/'), {}, 'about'),

    # Endpoint for remote admin
    url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),

)

urlpatterns += patterns('central.api_views',
    url(r'^api/', include(central.api_urls)),
)

urlpatterns += patterns('stats.views',
    url(r'^stats/', include(stats.urls)),
)

handler403 = 'central.views.handler_403'
handler404 = 'central.views.handler_404'
handler500 = 'central.views.handler_500'
