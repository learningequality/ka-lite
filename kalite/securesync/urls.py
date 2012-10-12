from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('securesync.api_views',
    url(r'^api/register$', 'register'),
    url(r'^api/session/create$', 'create_session'),
    url(r'^api/session/destroy$', 'destroy_session'),
    url(r'^api/models/count$', 'count_models'),
    url(r'^api/models/update$', 'update_models'),
)

urlpatterns = patterns('securesync.views',
    url(r'^register$', 'register'),
)
