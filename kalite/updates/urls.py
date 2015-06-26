from django.conf.urls import patterns, url
from django.conf import settings


urlpatterns = patterns(__package__ + '.views',
    url(r'^videos/$', 'update_videos', {}, 'update_videos'),
    url(r'^languages/$', 'update_languages', {}, 'update_languages')

)