from django.conf.urls.defaults import include, patterns, url

import settings

urlpatterns = patterns('securesync.views',
    url(r'^', include('securesync.devices.urls')),
    url(r'^', include('securesync.engine.urls')),
)

# An endpoint for remote administration of the distributed server
if not settings.CENTRAL_SERVER:
    urlpatterns += patterns('securesync.views',
        url(r'^cryptologin/$', 'crypto_login', {}, 'crypto_login'),
    )
