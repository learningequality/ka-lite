"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.http import HttpResponseServerError

import kalite.i18n.api_urls
import kalite.khanload.api_urls
import kalite.main.api_urls
import kalite.updates.api_urls


urlpatterns = patterns(__package__ + '.api_views',
    # For manipulating the static webpage to show data based on user state
    url(r'^status$', 'status', {}, 'status'),

    # Setting server time (RPi)
    url(r'^time_set/$', 'time_set', {}, 'time_set'),

    # Show pid for the running server (used bt stop to help kill the server)
    url(r'^getpid$', 'getpid', {}, 'getpid'),
)


# Khanload allows users to download data from a Khan Academy account
urlpatterns += patterns('kalite.khanload.api_views',
    url(r'^khanload/', include(kalite.khanload.api_urls)),
)

# Main exposes endpoints for loading/saving progress and topic tree info (search, etc)
urlpatterns += patterns('kalite.main.api_views',
    url(r'^', include(kalite.main.api_urls)),
)

# Updates allows server-client interactions when downloading / updating content and software
urlpatterns += patterns('kalite.updates.api_views',
    url(r'^', include(kalite.updates.api_urls)),
)

# i18n allows changing default languages for users
urlpatterns += patterns('kalite.i18n.api_views',
    url(r'^i18n/', include(kalite.i18n.api_urls)),
)


urlpatterns += patterns('',
    # toss out any requests made to actual KA site urls
    # Placed at the bottom, so that it's the last to be checked (not first)
    url(r'^v1/', lambda x: HttpResponseServerError("This is an assert--you should disable these calls from KA in the javascript code!")),
)
