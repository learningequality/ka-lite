from django.conf.urls import patterns, url, include
from .api_resources import TestLogResource, TestResource

urlpatterns = patterns(__package__ + '.api_views',
    url(r'^', include(TestLogResource().urls)),
    url(r'^', include(TestResource().urls)),
)