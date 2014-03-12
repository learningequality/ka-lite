from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse

import settings
from .models import Facility


def refresh_session_facility_info(request, facility_count):
    # Fix for #1211
    # Free time to refresh the facility info, which is otherwise cached for efficiency
    request.session["facility_count"] = facility_count
    request.session["facility_exists"] = request.session["facility_count"] > 0

class AuthFlags:
    def process_request(self, request):
        request.is_admin = False
        request.is_teacher = False
        request.is_logged_in = False
        request.is_django_user = False

        if request.user.is_authenticated():
            # Django user
            request.is_logged_in = True
            request.is_django_user = True
            if request.user.is_superuser:
                request.is_admin = True
            if "facility_user" in request.session:
                del request.session["facility_user"]

        elif "facility_user" in request.session:
            # Facility user
            if request.session["facility_user"].is_teacher:
                request.is_admin = True
                request.is_teacher = True
            request.is_logged_in = True

class FacilityCheck:
    def process_request(self, request):
        """
        Cache facility data in the session,
          while making sure anybody who can create facilities sees the real (non-cached) data
        """
        if not "facility_exists" in request.session or request.is_admin:
            # always refresh for admins, or when no facility exists yet.
            refresh_session_facility_info(request, facility_count=Facility.objects.count())

class LockdownCheck:
    def process_request(self, request):
        """
        Whitelist only a few URLs, otherwise fail.
        """
        if settings.LOCKDOWN and not request.is_logged_in and request.path not in [reverse("homepage"), reverse("login"), reverse("add_facility_student"), reverse("status")] and not request.path.startswith(settings.STATIC_URL):
            raise PermissionDenied()