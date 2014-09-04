from django.conf.urls import include, patterns, url

from .api_resources import FacilityResource, FacilityGroupResource, FacilityUserResource


urlpatterns = patterns(__package__ + '.api_views',
    url(r'^', include(FacilityResource().urls)),
    url(r'^', include(FacilityGroupResource().urls)),
    url(r'^', include(FacilityUserResource().urls)),
)
