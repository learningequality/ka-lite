from annoying.functions import get_object_or_None
from functools import partial

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import settings
from config.models import Settings
from securesync.models import Device, DeviceZone, Zone, Facility, FacilityUser


def central_server_only(handler):
    """
    Decorator that marks a function for use only on the central server.
    """
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            return Http404("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    """
    Decorator that marks a function for use only on a distributed server.
    """
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            return Http404(_("This path is only available on distributed servers."))
        return handler(*args, **kwargs)
    return wrapper_fn


def facility_from_request(handler=None, request=None, *args, **kwargs):
    """
    Goes through the request object to retrieve facility information, if possible.
    """
    assert handler or request
    if not handler:
        handler = lambda request, facility, *args, **kwargs: facility

    def wrapper_fn(request, *args, **kwargs):
        if kwargs.get("facility_id",None):
            facility = get_object_or_None(pk=facility_id)
        elif "facility" in request.GET:
            facility = get_object_or_None(Facility, pk=request.GET["facility"])
            if "set_default" in request.GET and request.is_admin and facility:
                Settings.set("default_facility", facility.id)
        elif "facility_user" in request.session:
            facility = request.session["facility_user"].facility
        elif Facility.objects.count() == 1:
            facility = Facility.objects.all()[0]
        else:
            facility = get_object_or_None(Facility, pk=Settings.get("default_facility"))
        return handler(request, *args, facility=facility, **kwargs)
    return wrapper_fn if not request else wrapper_fn(request=request, *args, **kwargs)


def facility_required(handler):
    """
    * Tries to get a facility from the request object.
    * If none exist, it tries to get the user to create one.
    * Otherwise, it fails, telling the user that a facility is required
        for whatever action hey were doing.
    """
    @facility_from_request
    def inner_fn(request, facility, *args, **kwargs):
        if facility:
            return handler(request, facility, *args, **kwargs)

        if Facility.objects.count() == 0:
            if request.is_admin:
                messages.error(request, _("To continue, you must first add a facility (e.g. for your school). ") \
                    + _("Please use the form below to add a facility."))
            else:
                messages.error(request,
                    _("You must first have the administrator of this server log in below to add a facility."))
            return HttpResponseRedirect(reverse("add_facility"))
        else:
            return facility_selection(request)

    return inner_fn


def get_user_from_request(handler=None, request=None, *args, **kwargs):
    """
    Gets ID of requested user (not necessarily the user logged in)
    """
    assert handler or request
    if not handler:
        handler = lambda request, user, *args, **kwargs: user

    def wrapper_fn(request, *args, **kwargs):
        user = get_object_or_None(FacilityUser, id=request.REQUEST.get("user"))
        user = user or request.session.get("facility_user", None)
        return handler(request, *args, user=user, **kwargs)
    return wrapper_fn if not request else wrapper_fn(request=request, *args, **kwargs)


@distributed_server_only
def require_login(handler):
    """
   (Level 1) Make sure that a user is logged in to the distributed server.
    """
    def wrapper_fn(request, *args, **kwargs):
        if request.user.is_authenticated() or "facility_user" in request.session:
            return handler(request, *args, **kwargs)

        # Failed.  Send different response for ajax vs non-ajax requests.
        raise PermissionDenied(_("You must be logged in to access this page."))
    return wrapper_fn


def require_admin(handler):
    """
    Level 2: Require an admin:
    * Central server: any user with an account
    * Distributed server: any Django admin or teacher.
    
    Note: different behavior for api_request or not
    """

    def wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)

        # Only here if user is not authenticated.
        # Don't redirect users to login for an API request.
        raise PermissionDenied(_("You must be logged in as an admin to access this page."))

    return wrapper_fn



def require_authorized_access_to_student_data(handler):
    """
    WARNING: this is a crappy function with a crappy name.
    
    This should only be used for limiting data access to single-student data.
    
    Students requesting their own data (either implicitly, without querystring params)
    or explicitly (specifying their own user ID) get through.
    Admins and teachers also get through.
    """

    @distributed_server_only
    @require_login
    def wrapper_fn_distributed(request, *args, **kwargs):
        """
        Everything is allowed for admins on distributed server.
        For students, they can only access their own account.
        """
        if getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)
        else: 
            user = get_user_from_request(request)
            if request.session.get("facility_user", None) == user:
                return handler(request, *args, **kwargs)
            else:
                raise PermissionDenied(_("You requested information for a user that you are not authorized to view."))
        return require_admin(handler)

    return require_authorized_admin(handler) if settings.CENTRAL_SERVER else wrapper_fn_distributed


def require_authorized_admin(handler):
    """
    Level 1.5 or 2.5 :) : require an admin user that has access to all requested objects.
    
    Central server: this is by organization permissions.
    Distributed server: you have to be an admin (Django admin/teacher), or requesting only your own user data.

    For testing purposes:
    * distributed server: superuser, teacher, student
    * central server: device not on zone/org, facility not on zone/org, zone not in org, zone with one org, zone with multi orgs, etc
    """

    @central_server_only
    @require_admin
    def wrapper_fn_central(request, *args, **kwargs):
        """
        The check for distributed servers already exists (require_login), so just use that below.
        All this nuance is for the central server only.
        """
        # inline import, to avoid unnecessary dependency on central server module
        #    on the distributed server.
        from central.models import Organization

        logged_in_user = request.user
        assert not logged_in_user.is_anonymous(), "Wrapped by login_required!"

        # Take care of superusers (Django admins).
        if logged_in_user.is_superuser:
            return handler(request, *args, **kwargs)


        # Objects we're looking to verify
        org = None; org_id      = kwargs.get("org_id", None)
        zone = None; zone_id     = kwargs.get("zone_id", None)
        facility = facility_from_request(request=request, *args, **kwargs)
        device = None; device_id   = kwargs.get("device_id", None)
        user = get_user_from_request(request=request, *args, **kwargs)

        # Validate user through facility
        if user:
            if not facility:
                facility = user.facility

        # Validate device through zone
        if device_id:
            device = get_object_or_404(Device, pk=device_id)
            if not zone_id:
                zone = device.get_zone()
                if not zone:
                    raise PermissionDenied("You requested device information for a device without a zone.  Only super users can do this!")
                zone_id = zone.pk

        # Validate device through zone
        if facility:
            if not zone_id:
                zone = facility.get_zone()
                if not zone:
                    raise PermissionDenied("You requested facility information for a facility with no zone.  Only super users can do this!")
                zone_id = zone.pk

        # Validate zone through org
        if zone_id:
            zone = get_object_or_404(Zone, pk=zone_id)
            if not org_id:
                # Have to check if any orgs are accessible to this user.
                for org in Organization.from_zone(zone):
                    if org.is_member(logged_in_user):
                        return handler(request, *args, **kwargs)
                raise PermissionDenied("You requested information from an organization that you're not authorized on.")

        if org_id:
            if org_id=="new":
                raise PermissionDenied("You requested information from an organization that you're not authorized on.")
            org = get_object_or_404(Organization, pk=org_id)
            if not org.is_member(logged_in_user):
                raise PermissionDenied("You requested information from an organization that you're not authorized on.")
            elif zone_id and zone and org.zones.filter(pk=zone.pk).count() == 0:
                raise PermissionDenied("This organization does not have permissions for this zone.")

        # Made it through, we're safe!
        return handler(request, *args, **kwargs)

    # This is where the actual distributed server check is done (require_admin)
    return wrapper_fn_central if settings.CENTRAL_SERVER else require_admin(handler)


def require_superuser(handler):
    """
    Level 4: require a Django admin (superuser)
    
    ***
    *** Note: Not yet used, nor tested. ***
    ***
    
    """
    def wrapper_fn(request, *args, **kwargs):
        if getattr(request.user, is_superuser, False):
            return handler(request, *args, **kwargs)
        else:
            raise PermissionDenied(_("Must be logged in as a superuser to access this endpoint."))
    return wrapper_fn
