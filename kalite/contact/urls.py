from django.conf.urls.defaults import patterns, include, url

import views


urlpatterns = patterns('contact.views',
    url(r'^thanks/?$',      'contact_thankyou', {}, 'contact_thankyou'),
    url(r'^subscribe/?$',   'contact_subscribe', {}, 'contact_subscribe'),
    url(r'^(?P<type>\w*)$', 'contact_wizard',   {}, 'contact_wizard'),
)