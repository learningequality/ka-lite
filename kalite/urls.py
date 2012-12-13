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
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

if settings.CENTRAL_SERVER:
    
    from central.feeds import RssSiteNewsFeed, AtomSiteNewsFeed

    urlpatterns += patterns('central.views',
        url(r'^$', 'homepage', {}, 'homepage'), 
        url(r'^delete_admin/(?P<org_id>\w+)/(?P<user_id>\w+)/$', 'delete_admin', {}, 'delete_admin'), 
        url(r'^delete_invite/(?P<org_id>\w+)/(?P<invite_id>\w+)/$', 'delete_invite', {}, 'delete_invite'), 
        url(r'^accounts/', include('registration.urls')),
        url(r'^organization/(?P<id>\w+)/$', 'organization_form', {}, 'organization_form'),
        url(r'^organization/(?P<org_id>\w+)/zone/(?P<id>\w+)/$', 'zone_form', {}, 'zone_form'),
        url(r'^organization/invite_action/(?P<invite_id>\w+)/$', 'org_invite_action', {}, 'org_invite_action'),
        url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/$', 'central_facility_admin', {}, 'central_facility_admin'),
        url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/new/$', 'central_facility_edit', {"id": "new"}, 'central_facility_add'),
        url(r'^organization/(?P<org_id>\w+)/zone/(?P<zone_id>\w+)/facility/(?P<id>\w+)/$', 'central_facility_edit', {}, 'central_facility_edit'),
        url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'), 
        url(r'^getstarted/$','get_started', {}, 'get_started'),
        url(r'^glossary/$', 'glossary', {}, 'glossary'),
        url(r'^feeds/rss/$', RssSiteNewsFeed(), {}, 'rss_feed'),
        url(r'^feeds/atom/$', AtomSiteNewsFeed(), {}, 'atom_feed'),
    )
    
    handler404 = 'main.views.central_404_handler'
    handler500 = 'main.views.central_500_handler'

else:
    
    urlpatterns += patterns('main.views',
        url(r'^exercisedashboard/$', 'exercise_dashboard', {}, 'exercise_dashboard'),
        url(r'^coachreports/$', 'coach_reports', {}, 'coach_reports'),
        url(r'^$', 'homepage', {}, 'homepage'),
        url(r'^update/$', 'update', {}, 'update'),
        url(r'^api/', include('main.api_urls')),
        
        # the following pattern is a catch-all, so keep it last:
        url(r'^(?P<splat>.+)/$', 'splat_handler', {}, 'splat_handler'),
    )
    
    handler404 = 'main.views.distributed_404_handler'
    handler500 = 'main.views.distributed_500_handler'
