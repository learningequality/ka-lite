from django.conf.urls import patterns, url, include
from django.conf import settings

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^$', 'landing_page', {}, 'coach_reports'),

    url(r'^student/$', 'student_view', {}, 'student_view'),
    url(r'^student/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'student_view', {}, 'student_view'),

    url(r'^api/', include(api_urls)),
)


#Else block url patterns can't be empty because we have a reverse match for test_view/test_detail_view

if "nalanda" in settings.CONFIG_PACKAGE:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^test/$', 'test_view', {}, 'test_view'),
        url(r'^test/(?P<test_id>\w+)/$', 'test_detail_view', {}, 'test_detail_view'),
        url(r'^spending_report/$', 'spending_report_view', {}, 'spending_report_view'),
        url(r'^spending_report/(?P<user_id>\w+)$', 'spending_report_detail_view', {}, 'spending_report_detail_view'),
    )
else:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^/$', 'test_view', {}, 'test_view'),
        url(r'^/$', 'test_detail_view', {}, 'test_detail_view'),
        url(r'^/$', 'spending_report_view', {}, 'spending_report_view'),
        url(r'^/(?P<user_id>\w+)$', 'spending_report_detail_view', {}, 'spending_report_detail_view'),
    )
