import datetime
import logging

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.six.moves import http_client


class CSPMiddleware:
    """
    Implements the Content-Security-Policy response header, which
    conforming user-agents can use to restrict the permitted sources
    of various content.
    See http://www.w3.org/TR/CSP/
    """

    def process_response(self, request, response):

        # Check for debug view
        status_code = response.status_code
        if not settings.DEBUG or status_code in (403, 404, 500):
            return response

        header = 'Content-Security-Policy'
        if getattr(settings, 'CSP_REPORT_ONLY', False):
            header += '-Report-Only'

        response[header] = "default-src 'self' 'unsafe-eval' 'unsafe-inline' data: *.learningequality.org{append_srcs}; img-src data: *; script-src 'self' *.learningequality.org 'unsafe-eval' 'unsafe-inline'"
        
        # Add potentially alternative hosts configured as central server
        if "learningequality.org" not in settings.CENTRAL_SERVER_HOST:
            response[header] = response[header].format(
                append_srcs=" " + settings.CENTRAL_SERVER_HOST
            )
        else:
            response[header] = response[header].format(append_srcs="")

        return response


class LockdownCheck:

    def process_request(self, request):
        """
        Whitelist only a few URLs, otherwise fail.
        """
        if (
                settings.LOCKDOWN and
                not request.is_logged_in and
                request.path not in [reverse("facility_user_signup"), reverse("dynamic_js"), reverse("dynamic_css")] and
                not request.path.startswith("/api/") and
                not request.path.startswith("/securesync/api/user/") and
                not request.path.startswith(settings.STATIC_URL) and
                not request.GET.get('login', '') == 'True'
        ):

            raise PermissionDenied()


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


class LogRequests:

    def process_response(self, request, response):
        logger = logging.getLogger('django.request')
        # This is added because somehow requests aren't being logged

        IGNORED_PATHS = (
            '/api/updates/progress',
        )
        if not any([True for r in IGNORED_PATHS if request.path.startswith(r)]):
            logger.info(
                "HTTP Request {} - Response: {}".format(
                    request.path,
                    response.status_code
                )
            )

        return response
