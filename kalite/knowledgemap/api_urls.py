from django.conf.urls import patterns, url, include

from .api_resources import KnowledgeMapExerciseResource


urlpatterns = patterns(__package__ + '.views',
    # TastyPie API Urls
    url(r'^', include(KnowledgeMapExerciseResource().urls)),
)