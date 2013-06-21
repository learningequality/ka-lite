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

    url(r'^table/$', 'old_coach_report', {}, 'old_coach_report'),
    url(r'^table/(?P<report_type>\w+)/$', 'old_coach_report', {}, 'old_coach_report'),

    url(r'^test/$', 'test', {}, 'test'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/mastery$',  'coach_reports', {}, 'coach_reports'),
#    url(r'(?P<student_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/effort$',  'scatter_data', {}, 'scatter_effort'),
#    url(r'(?P<subject_id>\w+)/(?P<topic_id>\w+)/(?P<exercise_id>\w+)/scatter$', 'scatter_data', {}, 'scatter_data'),

    url(r'^api/', include(coachreports.api_urls)),
)

