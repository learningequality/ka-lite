from django.conf.urls import patterns, include, url
from django.conf import settings

import kalite.student_testing.api_urls

#Else block url patterns can't be empty because we have a reverse match for test/test_list/current_unit and others.

if "nalanda" in settings.CONFIG_PACKAGE:
    urlpatterns = patterns(
        'kalite.student_testing.views',
        url(r'^api/', include(kalite.student_testing.api_urls)),
        url(r'^t/(?P<test_id>.+)/$', 'test', {}, 'test'),
        url(r'^list/$', 'test_list', {}, 'test_list'),
        url(r'^current_unit/$', 'current_unit', {}, 'current_unit'),
    )
else:
    urlpatterns = patterns(
        'kalite.student_testing.views',
        url(r'^/$', include(kalite.student_testing.api_urls)),
        url(r'^/$', 'test', {}, 'test'),
        url(r'^/$', 'test_list', {}, 'test_list'),
        url(r'^/$', 'current_unit', {}, 'current_unit'),
    )
