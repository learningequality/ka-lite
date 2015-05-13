from django.conf.urls import patterns, url, include
from .api_resources import TestLogResource, TestResource

urlpatterns = patterns('',
    url(r'^', include(TestLogResource().urls)),
    url(r'^', include(TestResource().urls)),
)