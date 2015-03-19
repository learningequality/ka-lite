from django.contrib.auth import logout
from django.contrib import messages
import datetime

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect


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
            # if (request.user.is_authenticated() or "facility_user" in request.session) and not request.is_admin:
            if request.is_student:
                current_datetime = datetime.datetime.now()
                
                # Timeout if idle time period is exceeded.
                # seconds =
                if ('last_activity' in request.session and
                    (current_datetime - request.session['last_activity']).seconds >
                        settings.SESSION_IDLE_TIMEOUT):
                    logout(request)
                    messages.add_message(request, messages.ERROR, 'Your session has been timed out')

                    if request.is_ajax():
                        response = HttpResponse(status=401)
                    else:
                        # Redirect to the login page if session has timed-out.
                        redirect_to = request.path + "?login"
                        response = HttpResponseRedirect(redirect_to)
                    return response
                else:
                    # Set last activity time in current session.
                    request.session['last_activity'] = current_datetime

        return None