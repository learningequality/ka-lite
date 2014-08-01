from django.conf.urls import include, patterns, url

from .api_resources import FacilityResource, GroupResource, TestLogResource


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^', include(FacilityResource().urls)),
    url(r'^', include(GroupResource().urls)),
    url(r'^', include(TestLogResource().urls)),
)
