from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(__package__ + '.api_views',
    url(r'save_attempt_log$', 'save_attempt_log', {}, 'save_attempt_log'),
)