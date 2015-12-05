"""
URLS that are API endpoints, usually producing some action and returning a JsonResponse

Note that most times, these patterns are all under /api/, due to the way
they're imported into the project's urls.py file.
"""
import os
from django.conf.urls import include, patterns, url
from django.http import HttpResponseServerError, HttpResponse

import kalite.i18n.api_urls
import kalite.coachreports.api_urls
import kalite.control_panel.api_urls
import kalite.contentload.api_urls
import kalite.main.api_urls
import kalite.updates.api_urls
import kalite.inline.api_urls

############ Inline narratives ############################################
urlpatterns = patterns('',
    url(r'^inline/narrative/', include(kalite.inline.api_urls))
)

# Let user to create the super user from browser
urlpatterns += patterns(__package__ + '.views',
    url(r'^django_user$', 'create_superuser'),
    url(r'^django_user_form$', 'add_superuser_form'),
)

# Khanload allows users to download data from a Khan Academy account
urlpatterns += patterns('kalite.khanload.api_views',
    url(r'^contentload/', include(kalite.contentload.api_urls)),
)

# Cherrpyserver allows querying the PID
urlpatterns += patterns('',
    url(r'^cherrypy/getpid$', lambda r: HttpResponse(os.getpid())),
)

# Main exposes endpoints for loading/saving progress and topic tree info (search, etc)
urlpatterns += patterns('kalite.main.api_views',
    url(r'^', include(kalite.main.api_urls)),
)

# Updates allows server-client interactions when downloading / updating content and software
urlpatterns += patterns('kalite.updates.api_views',
    url(r'^', include(kalite.updates.api_urls)),
)


# Control panel data export endpoints
urlpatterns += patterns('kalite.control_panel.api_views',
    url(r'^control_panel/', include(kalite.control_panel.api_urls)),
)

# Coach report endpoints for lazily getting data for reporting
urlpatterns += patterns('kalite.coachreports.api_views',
    url(r'^coachreports/', include(kalite.coachreports.api_urls)),
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
