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
from utils.internet import JsonResponse, JsonpResponse


def central_server_only(handler):
    """
    Decorator that marks a function for use only on the central server.
    """
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            raise Http404("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    """
    Decorator that marks a function for use only on a distributed server.
    """
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            raise Http404(_("This path is only available on distributed servers."))
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
        if kwargs.get("facility_id", None):  # avoid using blank
            facility = get_object_or_None(pk=kwargs["facility_id"])
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

