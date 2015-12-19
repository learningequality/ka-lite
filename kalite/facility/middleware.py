"""
"""
import os

from annoying.decorators import render_to

from django.conf import settings
from django.core.management import call_command
from django.db import DatabaseError, connection
from django.db.models import signals
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Facility

from fle_utils.config.models import Settings
from fle_utils.general import get_host_name

FACILITY_CACHE_STALE = False

@ensure_csrf_cookie
@render_to("facility/facility_config.html")
def config_form(request, database):
    """
    Render the template for configuration form, passing in database information
    
    @param database: a dictionary containing the following info:
        { "need_update" : does the user need an update?
          "superuser" : does the superuser exist?
          "default_hostname" : what will the hostname default to, if User
                               chooses not to configure one? 
        }
    """
    return database

def is_configured():
    """
    Checks whether a system has been configured. For now, being configured
    simply means that a superuser exists. 
    """
    database = False
    superuser = False
    need_update = False

    # Check if database file exists
    database_kind = settings.DATABASES["default"]["ENGINE"]
    database_file =  (
        "sqlite" in database_kind \
                and settings.DATABASES["default"]["NAME"]) or None


    if database_file and os.path.exists(database_file):
        database = True

        # Check for database version, if mismatch, ask user to update
        # try:
    from kalite.version import VERSION

    # If version in database not set, it is probably the first
    # time running this version of KA Lite, but they haven't run setup
    if not Settings.get("database_version"):
        Settings.set("database_version", VERSION)

    # Otherwise, if database is already versioned, check
    # to see if it matches most updated version available
    assert Settings.get("database_version") == VERSION

    return { "need_update" : need_update,
             "superuser" : superuser,
             "default_hostname" : get_host_name() }


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
    def process_response(self, request, response):
        """
        Display configuration page if facility does not have a superuser, 
        or if there are updates available. 
        """

        # Only intercept text/html responses to prevent interfering with
        # static files
        if response['Content-Type'].split(';')[0] == 'text/html': 
            db_exists = is_configured()
            if db_exists['superuser'] and not db_exists['need_update']:
                return response

            # If device isn't configured, and user is trying to access KA Lite 
            # for the first time, load the form page to configure settings
            if request.path != '/facility/config/' and \
                    request.path != '/securesync/api/dl_progress':
            
                return config_form(request, db_exists)

        return response
