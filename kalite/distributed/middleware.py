from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse


class LockdownCheck:
    def process_request(self, request):
        """
        Whitelist only a few URLs, otherwise fail.
        """
        if settings.LOCKDOWN and not request.is_logged_in and request.path not in [reverse("homepage"), reverse("login"), reverse("facility_user_signup"), reverse("status")] and not request.path.startswith(settings.STATIC_URL):
            raise PermissionDenied()
