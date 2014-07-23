from django.conf.urls import include, patterns, url

from .api_resources import FacilityResource


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^', include(FacilityResource().urls)),
)
