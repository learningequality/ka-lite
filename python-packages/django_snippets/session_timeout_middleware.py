from django.contrib.auth import logout
from django.contrib import messages
import datetime

from django.conf import settings

import logging

class SessionIdleTimeout:
    """
    Middleware class to timeout a session after a specified time period.
    Modified from:
    https://github.com/subhranath/django-session-idle-timeout
    """
    def process_request(self, request):
        # Only do timeout if enabled
        if settings.SESSION_IDLE_TIMEOUT:
            # Timeout is done only for authenticated logged in *student* users.
            if (request.user.is_authenticated() or "facility_user" in request.session) and not request.is_admin:
                current_datetime = datetime.datetime.now()
                
                # Timeout if idle time period is exceeded.
                if (request.session.has_key('last_activity')
                    and
                    (current_datetime - request.session['last_activity']).seconds >
                    settings.SESSION_IDLE_TIMEOUT):
                    logout(request)
                    messages.add_message(request, messages.ERROR, 'Your session has been timed out.')
                # Set last activity time in current session.
                else:
                    request.session['last_activity'] = current_datetime
        return None