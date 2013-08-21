from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('updates.api_views',
    url(r'^progress$', 'check_update_progress', {}, 'check_update_progress'),
    url(r'^cancel$', 'cancel_update_progress', {}, 'cancel_update_progress'),
)