"""
This sub-module defines models related to user logins and permissions.
If any sub-module really could be separated from securesync, it would be this:
these models use the machinery of engine and devices, they are simply data.
"""
import re
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

from .middleware import refresh_session_facility_info
from .models import Facility
from fle_utils.config.models import Settings
from securesync.models import Device


def facility_from_request(handler=None, request=None, *args, **kwargs):
    """
    Goes through the request object to retrieve facility information, if possible.
    """
    assert handler or request
    if not handler:
        handler = lambda request, facility, *args, **kwargs: facility

    def facility_from_request_wrapper_fn(request, *args, **kwargs):
        facility = None

        if kwargs.get("facility_id", None):  # avoid using blank
            # Facility passed in directly
            facility = get_object_or_None(Facility, pk=kwargs["facility_id"])
            del kwargs["facility_id"]

        if not facility and "facility" in request.GET:
            # Facility from querystring
            facility = get_object_or_None(Facility, pk=request.GET["facility"])

        if facility:
            pass

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

        if "set_default" in request.GET and request.is_admin and facility:
            Settings.set("default_facility", facility.id)

        if facility or "facility" not in kwargs:  # this syntax allows passed in facility param to work.
            kwargs["facility"] = facility
        return handler(request, *args, **kwargs)

    return facility_from_request_wrapper_fn if not request else facility_from_request_wrapper_fn(request=request, *args, **kwargs)


def facility_required(handler):
    """
    * Tries to get a facility from the request object.
    * If none exist, it tries to get the user to create one.
    * Otherwise, it fails, telling the user that a facility is required
        for whatever action hey were doing.
    """
    @facility_from_request
    def facility_required_inner_fn(request, facility, *args, **kwargs):
        if facility:
            return handler(request, facility=facility, *args, **kwargs)

        if not request.session["facility_exists"]:
            if request.is_admin:
                messages.warning(request, _("To continue, you must first add a facility (e.g. for your school). ") \
                    + _("Please use the form below to add a facility."))
            else:
                messages.warning(request,
                    _("You must first have the administrator of this server log in below to add a facility."))
            zone_id = getattr(Device.get_own_device().get_zone(), "id", "None")
            return HttpResponseRedirect(reverse("add_facility", kwargs={"zone_id": zone_id}))

        else:
            @render_to("facility/facility_selection.html")
            def facility_selection(request):
                facilities = list(Facility.objects.all())
                refresh_session_facility_info(request, len(facilities))

                # Choose the path template
                cp_path_match = re.match(r"^(.*\/facility\/)[^/]+(\/.*)$", request.path)
                if cp_path_match:
                    path_template = "%s%%(facility_id)s%s" % cp_path_match.groups()
                else:
                    path_template="%(path)s?%(querystring)s&facility=%(facility_id)s"

                selection_paths = {}
                for facility in facilities:
                    selection_paths[facility.id] = path_template % ({
                        "path": request.path,
                        "querystring": "",
                        "facility_id": facility.id,
                    })
                return {
                    "facilities": facilities,
                    "selection_paths": selection_paths,
                }
            return facility_selection(request)

    return facility_required_inner_fn
