from django.conf.urls import patterns, url, include
from django.conf import settings

from . import api_urls


urlpatterns = patterns(__package__ + '.views',
    url(r'^teach/', 'coach_reports', {}, 'coach_reports'),

    url(r'^student/$', 'student_view', {}, 'student_view'),
    url(r'^student/(?P<xaxis>[^/]+)/(?P<yaxis>[^/]+)/$', 'student_view', {}, 'student_view'),

    url(r'^api/', include(api_urls)),
)
