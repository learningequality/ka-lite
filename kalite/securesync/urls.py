from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('',

    url(r'^session/create$', views.create_session),
    url(r'^session/destroy$', views.destroy_session),
    url(r'^models/count$', views.count_models),
    url(r'^models/update$', views.update_models),
    
)
