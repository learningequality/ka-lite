import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse


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
                not request.path.startswith("/securesync/api/user/status") and
                not request.path.startswith(settings.CONTENT_DATA_URL) and
                not request.path.startswith(settings.STATIC_URL) and
                not request.GET.get('login', '') == 'True'
        ):

            raise PermissionDenied()


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
