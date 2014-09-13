from django.conf.urls import patterns, url, include

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

    url(r'^test/$', 'test_view', {}, 'test_view'),
    url(r'^test/(?P<test_id>\w+)/$', 'test_detail_view', {}, 'test_detail_view'),

    url(r'^api/', include(api_urls)),
)
