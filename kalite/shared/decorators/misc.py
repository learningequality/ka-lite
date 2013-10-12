from annoying.decorators import render_to
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
            # Facility passed in directly
            facility = get_object_or_None(Facility, pk=kwargs["facility_id"])

        elif "facility" in request.GET:
            # Facility from querystring
            facility = get_object_or_None(Facility, pk=request.GET["facility"])
            if "set_default" in request.GET and request.is_admin and facility:
                Settings.set("default_facility", facility.id)

        elif settings.CENTRAL_SERVER:  # following options are distributed-only
            facility = None

        elif "facility_user" in request.session:
            # Facility from currently logged-in facility user
            facility = request.session["facility_user"].facility

        elif request.session["facility_count"] == 1:
            # There's only one facility
            facility = Facility.objects.all()[0]

        elif request.session["facility_count"] > 0:
            # There are multiple facilities--try to grab the default
            facility = get_object_or_None(Facility, pk=Settings.get("default_facility"))

        else:
            # There's nothing; don't bother even hitting the DB
            facility = None

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

        if not request.session["facility_exists"]:
            if request.is_admin:
                messages.warning(request, _("To continue, you must first add a facility (e.g. for your school). ") \
                    + _("Please use the form below to add a facility."))
            else:
                messages.warning(request,
                    _("You must first have the administrator of this server log in below to add a facility."))
            return HttpResponseRedirect(reverse("add_facility"))
        else:
            @distributed_server_only
            @render_to("securesync/facility_selection.html")
            def facility_selection(request):
                facilities = Facility.objects.all()
                context = {"facilities": facilities}
                return context
            return facility_selection(request)

    return inner_fn

