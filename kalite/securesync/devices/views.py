import urllib
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

import settings
from config.models import Settings
from main.models import UserLog
from securesync import crypto
from securesync.devices.api_client import RegistrationClient
from securesync.forms import RegisteredDevicePublicKeyForm, FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from securesync.models import SyncSession, Device, Facility, FacilityGroup, Zone
from shared.decorators import require_admin, central_server_only, distributed_server_only, facility_required, facility_from_request
from shared.jobs import force_job


def register_public_key(request):
    if settings.CENTRAL_SERVER:
        return register_public_key_server(request)
    else:
        return register_public_key_client(request)


def set_as_registered():
    force_job("syncmodels", "Secure Sync", "HOURLY")  # now launches asynchronously
    Settings.set("registered", True)


@require_admin
@render_to("securesync/register_public_key_client.html")
def register_public_key_client(request):
    own_device = Device.get_own_device()
    if own_device.get_zone():
        set_as_registered()
        return {"already_registered": True}
    client = RegistrationClient()
    if client.test_connection() != "success":
        return {"no_internet": True}
    reg_response = client.register()
    reg_status = reg_response.get("code")
    if reg_status == "registered":
        set_as_registered()
        return {"newly_registered": True}
    if reg_status == "device_already_registered":
        set_as_registered()
        return {"already_registered": True}
    if reg_status == "public_key_unregistered":
        # Callback url used to redirect to the distributed server url
        #   after successful registration on the central server.
        return {
            "unregistered": True,
            "registration_url": client.path_to_url(
                reverse("register_public_key") + "?" + urllib.quote(own_device.public_key)
            ),
            "central_login_url": "%s://%s/accounts/login" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST),
            "callback_url": request.build_absolute_uri(reverse("register_public_key")),
        }
    error_msg = reg_response.get("error", "")
    if error_msg:
        return {"error_msg": error_msg}
    return HttpResponse(_("Registration status: ") + reg_status)


@central_server_only
@login_required
@render_to("securesync/register_public_key_server.html")
def register_public_key_server(request):
    if request.method == 'POST':
        form = RegisteredDevicePublicKeyForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            zone_id = form.data["zone"]
            org_id = Zone.objects.get(id=zone_id).get_org().id

            callback_url = form.cleaned_data.get("callback_url", None)
            if callback_url:
                # New style: go directly to the origin page, which will force a sync to occur (no reason to ping refresh)
                #   This is better for the current force_job
                return HttpResponseRedirect(callback_url)
            else:
                # Old style, for clients that don't send a callback url
                messages.success(request, _("The device's public key has been successfully registered. You may now close this window."))
                return HttpResponseRedirect(reverse("zone_management", kwargs={'org_id': org_id, 'zone_id': zone_id}))

    else:
        # This is hackish--we now create default organizations and zones for users, based on their
        #   registration information.  For previous users, however, we don't.  And we don't
        #   give any links / instructions for creating zones when they get here.
        # So, rather than block them, let's create an org and zone for them, so that
        #   at least they can proceed directly.
        if request.user.organization_set.count() == 0:
            # Localizing central-only import
            from central.models import Organization
            org = Organization(name="Your organization", owner=request.user)
            org.save()
            org.add_member(request.user)
            org.save()
        if not sum([org.zones.count() for org in request.user.organization_set.all()]):
            org = request.user.organization_set.all()[0]
            zone = Zone(name="Default zone")
            zone.save()
            org.add_zone(zone)

        # callback_url: 0.10.3 and higher (distributed server)
        # prev: 0.10.3 and higher (central server)
        #
        # Note: can't use referer, because this breaks if the user is redirected
        #   to the central server login page--gets confusing.
        form = RegisteredDevicePublicKeyForm(
            request.user,
            callback_url = request.REQUEST.get("callback_url") or request.REQUEST.get("prev"),
        )
    return {
        "form": form,
    }


