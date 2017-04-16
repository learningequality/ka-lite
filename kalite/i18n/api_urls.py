from django.conf.urls import patterns, url


urlpatterns = patterns(__package__ + '.api_views',
    url(r'set_default_language/$', 'set_server_or_user_default_language', {}, 'set_default_language'),
)
