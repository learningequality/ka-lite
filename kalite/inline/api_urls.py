from django.conf.urls import include, patterns, url

urlpatterns = patterns (__package__ + '.api_views',   
    url(r'^(?P<narrative_id>[\w/]+)', 'narrative_view', name="narrative")
)