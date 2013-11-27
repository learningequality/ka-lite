from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('research.views',
    url(r'^$', 'control_flow', {}, 'control_flow'),
)