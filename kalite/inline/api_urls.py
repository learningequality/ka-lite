from django.conf.urls import include, patterns, url

from .api_resources import NarrativeResource


urlpatterns = patterns('',
    url(r'^', include(NarrativeResource().urls))
)