"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponseServerError

import khanload.api_urls
import main.api_urls
import updates.api_urls


urlpatterns = patterns('distributed.api_views',
    # For manipulating the static webpage to show data based on user state
    url(r'^status$', 'status', {}, 'status'),

    # For launching an external player (RPi)
    url(r'^launch_mplayer$', 'launch_mplayer', {}, 'launch_mplayer'),

    # Setting server time (RPi)
    url(r'^time_set/$', 'time_set', {}, 'time_set'),

    # Show pid for the running server (used bt stop to help kill the server)
    url(r'^getpid$', 'getpid', {}, 'getpid'),
)


# Khanload allows users to download data from a Khan Academy account
urlpatterns += patterns('khanload.api_views',
    url(r'^khanload/', include(khanload.api_urls)),
)

# Main exposes endpoints for loading/saving progress and topic tree info (search, etc)
urlpatterns += patterns('main.api_views',
    url(r'^', include(main.api_urls)),
)

# Updates allows server-client interactions when downloading / updating content and software
urlpatterns += patterns('updates.api_views',
    url(r'^', include(updates.api_urls)),
)


urlpatterns += patterns('',
    # toss out any requests made to actual KA site urls
    # Placed at the bottom, so that it's the last to be checked (not first)
    url(r'^v1/', lambda x: HttpResponseServerError("This is an assert--you should disable these calls from KA in the javascript code!")),
)
