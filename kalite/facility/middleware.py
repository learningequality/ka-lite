"""
"""
from django.conf import settings
from django.db.models import signals
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from .models import Facility
from .views import add_facility_teacher

FACILITY_CACHE_STALE = False

def is_configured():
    """
    Checks whether a system has been configured. For now, it simply 
    checks if a superuser exists.
    """
    try:
        u = User.objects.get(is_superuser=True)
    except ObjectDoesNotExist:
        return False

    return True

def refresh_session_facility_info(request, facility_count):
    # Fix for #1211
    # Free time to refresh the facility info, which is otherwise cached for efficiency
    request.session["facility_count"] = facility_count
    request.session["facility_exists"] = request.session["facility_count"] > 0

    # To enable simplified login, also list the id and names of all facilities in the session object.
    # This keeps it cached so that the status api call can return this to the client side
    # without significantly increasing DB load on every status call.
    request.session["facilities"] = [{"id": id, "name": name} for id, name in Facility.objects.values_list("id", "name")]

def flag_facility_cache(**kwargs):
    global FACILITY_CACHE_STALE
    FACILITY_CACHE_STALE = True

post_save.connect(flag_facility_cache, sender=Facility)

class AuthFlags:
    def process_request(self, request):
        request.is_admin = False
        request.is_teacher = False
        request.is_student = False
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
            else:
                request.is_student = True
            request.is_logged_in = True


class FacilityCheck:
    def process_request(self, request):
        """
        Cache facility data in the session,
          while making sure anybody who can create facilities sees the real (non-cached) data
        """
        if not "facility_exists" in request.session or FACILITY_CACHE_STALE:
            # always refresh for admins, or when no facility exists yet.
            refresh_session_facility_info(request, facility_count=Facility.objects.count())

class ConfigCheck:
    def process_request(self, request):
        """
        Display configuration modal if facility does not have all of the
        required settings yet.
        """
        if is_configured():
            return None

        #does_database_exist(request)
        #return HttpResponse("not configured.... ")
        #response = TemplateResponse("not configured")
        #return response
