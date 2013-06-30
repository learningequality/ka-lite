from django.conf.urls.defaults import patterns, url, include

import coachreports.api_urls

urlpatterns = patterns('coachreports.views',
    url(r'^$', 'landing_page', {}, 'coach_reports'),

    url(r'^scatter/$', 'scatter_view', {}, 'scatter_view'),
    url(r'^scatter/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'scatter_view', {}, 'scatter_view'),

    url(r'^timeline/$', 'timeline_view', {}, 'timeline_view'),
    url(r'^timeline/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'timeline_view', {}, 'timeline_view'),

    url(r'^student/$', 'student_view', {}, 'student_view'),
    url(r'^student/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'student_view', {}, 'student_view'),

    url(r'^table/$', 'tabular_view', {}, 'tabular_view'),
    url(r'^table/(?P<report_type>\w+)/$', 'tabular_view', {}, 'tabular_view'),

    url(r'^api/', include(coachreports.api_urls)),
)

