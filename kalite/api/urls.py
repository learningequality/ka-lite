from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('',

    url(r'^v1/', lambda x: HttpResponse("{}")),
    
)
