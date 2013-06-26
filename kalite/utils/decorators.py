from annoying.functions import get_object_or_None
from functools import partial

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

import settings
from central.models import Organization
from config.models import Settings
from securesync.models import Device, DeviceZone, Zone, Facility
#from securesync.views import facility_selection



def require_admin(handler):
    return require_admin_shared(handler, api_request=False)

def require_admin_api(handler):
    return require_admin_shared(handler, api_request=True)

def require_admin_shared(handler, api_request=False):
    def wrapper_fn(request, *args, **kwargs):
        if (settings.CENTRAL_SERVER and request.user.is_authenticated()) or getattr(request, "is_admin", False):
            return handler(request, *args, **kwargs)

        # Only here if user is not authenticated.
        # Don't redirect users to login for an API request.
        if api_request:
            return HttpResponseForbidden("You must be logged in as an admin to access this API endpoint.")
        else:
            # Translators: Please ignore the html tags e.g. "Please login as one below, or <a href='%s'>go to home.</a>" is simply "Please login as one below, or go to home."
            messages.error(request, mark_safe(_("To view the page you were trying to view, you need to be logged in as a teacher or an admin. Please login as one below, or <a href='%s'>go to home.</a>") % reverse("homepage")))
            return HttpResponseRedirect(reverse("login") + "?next=" + request.path)

    return wrapper_fn#partial(wrapper_fn, api_request=api_request)
    
def require_login(handler):
    def wrapper_fn(request, *args, **kwargs):
        if request.user.is_authenticated() or "facility_user" in request.session:
            return handler(request, *args, **kwargs)
        # Translators: Please ignore the html tags e.g. "Please login as one below, or <a href='%s'>go to home.</a>" is simply "Please login as one below, or go to home."
        messages.error(request, mark_safe(_("To view the page you were trying to view, you need to be logged in. Please login as one below, or <a href='%s'>go to home.</a>") % reverse("homepage")))
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
    return wrapper_fn
    


def central_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            return HttpResponseNotFound("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            return HttpResponseNotFound(_("This path is only available on distributed servers."))
        return handler(*args, **kwargs)
    return wrapper_fn
    


def authorized_login_required(handler):
    """A generic function that determines whether a user has permissions to view a page.
    
    Central server: this is by organization permissions.
    Distributed server: you have to be an admin.
    """
    
    def wrapper_fn(request, *args, **kwargs):
        user = request.user
        assert not user.is_anonymous(), "Wrapped by login_required!"

        if user.is_superuser:
            return handler(request, *args, **kwargs)
        
        org = None; org_id      = kwargs.get("org_id", None)
        zone = None; zone_id     = kwargs.get("zone_id", None)
        device = None; device_id   = kwargs.get("device_id", None)
        facility = None; facility_id = kwargs.get("facility_id", None)
        
        # Validate device through zone
        if device_id:
            device = get_object_or_404(Device, pk=device_id)
            if not zone_id:
                zone = device.get_zone()
                if not zone:
                    return HttpResponseForbidden("Device, no zone, no DeviceZone")
                zone_id = zone.pk
                
        # Validate device through zone
        if facility_id:
            facility = get_object_or_404(Facility, pk=facility_id)
            if not zone_id:
                zone = facility.get_zone()
                if not zone:
                    return HttpResponseForbidden("Facility, no zone")
                zone_id = zone.pk
                
        # Validate zone through org
        if zone_id:
            zone = get_object_or_404(Zone, pk=zone_id)
            if not org_id:
                orgs = Organization.from_zone(zone)
                if len(orgs) != 1:
                    return HttpResponseForbidden("Zone, no org")
                org = orgs[0]
                org_id = org.pk

        if org_id:
            if org_id=="new":
                return HttpResponseForbidden("Org")
            org = get_object_or_404(Organization, pk=org_id)
            if not org.is_member(request.user):
                return HttpResponseForbidden("Org")
            elif zone_id and zone and org.zones.filter(pk=zone.pk).count() == 0:
                return HttpResponseForbidden("This organization does not have permissions for this zone.")
    
        # Made it through, we're safe!
        return handler(request, *args, **kwargs)
        
    
    return wrapper_fn if settings.CENTRAL_SERVER else require_admin(handler)
    