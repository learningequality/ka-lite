"""
"""
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponseServerError

import khanload.api_urls
import main.api_urls
import updates.api_urls


# Note that these patterns are all under /api/,
# due to the way they've been included into main/urls.py
urlpatterns = patterns('distributed.api_views',

    url(r'^launch_mplayer$', 'launch_mplayer', {}, 'launch_mplayer'),

    url(r'^status$', 'status', {}, 'status'),

    #API endpoint for setting server time
    url(r'^time_set/$', 'time_set', {}, 'time_set'),

    # show pid for the running server (used bt stop to help kill the server)
    url(r'^getpid$', 'getpid', {}, 'getpid'),
)


urlpatterns += patterns('khanload.api_views',
    url(r'^khanload/', include(khanload.api_urls)),
)

urlpatterns += patterns('main.api_views',
    url(r'^', include(main.api_urls)),
)

urlpatterns += patterns('updates.api_views',
    url(r'^', include(updates.api_urls)),
)


# Placed at the bottom, so that it's the last to be checked (not first)
urlpatterns += patterns('',
    # toss out any requests made to actual KA site urls
    url(r'^v1/', lambda x: HttpResponseServerError("This is an assert--you should disable these calls from KA in the javascript code!")),
)
