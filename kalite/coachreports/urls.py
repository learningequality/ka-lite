from django.conf.urls import patterns, url, include
from django.conf import settings

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^$', 'landing_page', {}, 'coach_reports'),

    url(r'^scatter/$', 'scatter_view', {}, 'scatter_view'),
    url(r'^scatter/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'scatter_view', {}, 'scatter_view'),

    url(r'^timeline/$', 'timeline_view', {}, 'timeline_view'),
    url(r'^timeline/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'timeline_view', {}, 'timeline_view'),

    url(r'^student/$', 'student_view', {}, 'student_view'),
    url(r'^student/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'student_view', {}, 'student_view'),

    url(r'^table/$', 'tabular_view', {}, 'tabular_view'),
    url(r'^table/(?P<report_type>\w+)/$', 'tabular_view', {}, 'tabular_view'),


    url(r'^spending_report/$', 'spending_report_view', {}, 'spending_report_view'),
    url(r'^spending_report/(?P<user_id>\w+)$', 'spending_report_detail_view', {}, 'spending_report_detail_view'),

    url(r'^api/', include(api_urls)),
)


#Else block url patterns can't be empty because we have a reverse match for test_view/test_detail_view

if "Nalanda" in settings.CONFIG_PACKAGE:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^test/$', 'test_view', {}, 'test_view'),
        url(r'^test/(?P<test_id>\w+)/$', 'test_detail_view', {}, 'test_detail_view'),
    )
else:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^/$', 'test_view', {}, 'test_view'),
        url(r'^/$', 'test_detail_view', {}, 'test_detail_view'),
    )
