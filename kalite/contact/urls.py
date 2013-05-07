from django.conf.urls.defaults import patterns, include, url

import views


urlpatterns = patterns('contact.views',
    url(r'^$', 'contact_wizard',   {}, 'contact_wizard'),
    url(r'^thanks/?$', 'contact_thankyou', {}, 'contact_thankyou'),
)