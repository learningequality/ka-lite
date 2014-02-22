"""
This sub-module defines models related to user logins and permissions.
If any sub-module really could be separated from securesync, it would be this:
these models use the machinery of engine and devices, they are simply data.
"""
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import settings
from .middleware import refresh_session_facility_info
from .models import Facility
from config.models import Settings
from securesync.models import Device
from testing.asserts import distributed_server_only
from utils.internet import JsonResponse, JsonpResponse


def facility_from_request(handler=None, request=None, *args, **kwargs):
    """
    Goes through the request object to retrieve facility information, if possible.
    """
    from .models import Facility
    assert handler or request
    if not handler:
        handler = lambda request, facility, *args, **kwargs: facility

    def wrapper_fn(request, *args, **kwargs):
        if kwargs.get("facility_id", None):  # avoid using blank
            # Facility passed in directly
            facility = get_object_or_None(Facility, pk=kwargs["facility_id"])
            del kwargs["facility_id"]

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
            if Settings.get("default_facility"):
                # There are multiple facilities--try to grab the default
                facility = get_object_or_None(Facility, pk=Settings.get("default_facility"))

            elif Facility.objects.filter(Q(signed_by__isnull=True) | Q(signed_by=Device.get_own_device())).count() == 1:
                # Default to a locally created facility (if there are multiple, and none are specified)
                facility = Facility.objects.filter(Q(signed_by__isnull=True) | Q(signed_by=Device.get_own_device()))[0]

            else:
                facility = None
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
            @render_to("facility/facility_selection.html")
            def facility_selection(request):
                facilities = list(Facility.objects.all())
                refresh_session_facility_info(request, len(facilities))
                context = {"facilities": facilities}
                return context
            return facility_selection(request)

    return inner_fn

