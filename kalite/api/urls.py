from django.http import HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('',

    url(r'^v1/user/exercises/(?P<exercise>\w+)/problems/(?P<num>\d+)/attempt$', views.problem_attempt),
    
)
