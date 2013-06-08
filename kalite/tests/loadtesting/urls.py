from django.http import HttpResponse, HttpResponseRedirect
from django.conf.urls.defaults import patterns, include, url
import views

urlpatterns = patterns('tests.loadtesting.views',
    
    url(r'^$', 'load_test', {}, 'load_test'),

)
