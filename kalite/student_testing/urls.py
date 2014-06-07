from django.conf.urls import patterns, include, url

import student_testing.api_urls

urlpatterns = patterns(
    'student_testing.views',
    url(r'^api/', include(student_testing.api_urls)),
    url(r'^t/(?P<test_id>.+)/$', 'test', {}, 'test'),
    url(r'^list/$', 'test_list', {}, 'test_list'),
)
