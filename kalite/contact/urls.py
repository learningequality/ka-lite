from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('contact.views',
    url(r'^thanks/?$',      'contact_thankyou', {}, 'contact_thankyou'),
    url(r'^subscribe/?$',   'contact_subscribe', {}, 'contact_subscribe'),
    url(r'^$', 'contact_wizard', {}, 'contact_wizard'),
    url(r'^(?P<type>\w*)/$', 'contact_wizard', {}, 'contact_wizard'),
)