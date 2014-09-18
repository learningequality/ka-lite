from django.conf.urls import patterns, include, url

import kalite.student_testing.api_urls

urlpatterns = patterns(
    'student_testing.views',
    url(r'^api/', include(kalite.student_testing.api_urls)),
    url(r'^t/(?P<test_id>.+)/$', 'test', {}, 'test'),
    url(r'^list/$', 'test_list', {}, 'test_list'),
    url(r'^current_unit/$', 'current_unit', {}, 'current_unit'),
)
