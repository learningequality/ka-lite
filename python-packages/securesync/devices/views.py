"""
"""
import requests
import urllib
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

from .api_client import RegistrationClient
from .forms import RegisteredDevicePublicKeyForm
from .models import Device, Zone, RegisteredDevicePublicKey
from .. import crypto
from ..engine.models import SyncSession
from fle_utils.chronograph.utils import force_job
from fle_utils.config.models import Settings
from fle_utils.internet.classes import JsonResponse
from fle_utils.internet.decorators import allow_jsonp


def register_public_key(request):
    if not settings.CENTRAL_SERVER:
        return register_public_key_client(request)
    elif request.REQUEST.get("auto") == "True":
        return register_public_key_server_auto(request)
    else:
        return register_public_key_server(request)


def initialize_registration():
    force_job("syncmodels", "Secure Sync", "HOURLY")  # now launches asynchronously


@login_required
@render_to("securesync/register_public_key_client.html")
def register_public_key_client(request):

    # Delete the registration state from the session to ensure it is refreshed next pageload
    del request.session["registered"]

    own_device = Device.get_own_device()
    if own_device.is_registered():
        initialize_registration()
        if request.next:
            return HttpResponseRedirect(request.next)
        else:
            return {"already_registered": True}

    client = RegistrationClient()
    if client.test_connection() != "success":
        return {"no_internet": True}

    reg_response = client.register()
    reg_status = reg_response.get("code")
    if reg_status == "registered":
        initialize_registration()
        if request.next:
            return HttpResponseRedirect(request.next)
        else:
            return {"newly_registered": True}
    elif reg_status == "device_already_registered":
        initialize_registration()
        if request.next:
            return HttpResponseRedirect(request.next)
        else:
            return {"already_registered": True}
    elif reg_status == "public_key_unregistered":
        # Callback url used to redirect to the distributed server url
        #   after successful registration on the central server.
        return {
            "unregistered": True,
            "auto_registration_url": client.get_registration_url(auto=True),
            "classic_registration_url": client.get_registration_url(
                callback_url=request.build_absolute_uri(reverse("register_public_key"))
            ),
            "central_login_url": "%s://%s/accounts/login" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST),
        }

    error_msg = reg_response.get("error", "")
    if error_msg:
        return central_server_down_or_error(error_msg)

    return HttpResponse(_("Registration status: ") + reg_status)


def central_server_down_or_error(error_msg):
    """ If the central server is down, return a context that says so.
    Otherwise, pass along the actual error returned by the central server.
    error_msg: a string
    """
    if error_msg:
        if requests.get(settings.CENTRAL_SERVER_URL).status_code != 200:
            return {"error_msg": _("Central Server is not reachable; please try again after some time.")}
        else:
            return {"error_msg": error_msg}


#@central_server_only
@login_required
@render_to("securesync/register_public_key_server.html")
def register_public_key_server(request):

    if request.method == 'POST':
        form = RegisteredDevicePublicKeyForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            zone_id = form.data["zone"]

            callback_url = form.cleaned_data.get("callback_url", None)
            if callback_url:
                # New style: go directly to the origin page, which will force a sync to occur (no reason to ping refresh)
                #   This is better for the current force_job
                return HttpResponseRedirect(callback_url)
            else:
                # Old style, for clients that don't send a callback url
                messages.success(request, _("The device's public key has been successfully registered. You may now close this window."))
                return HttpResponseRedirect(reverse("zone_management", kwargs={'zone_id': zone_id}))

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


@allow_jsonp
#@central_server_only
def register_public_key_server_auto(request):
    """This function allows an anonymous client to request a device key
    to be associated with a new zone.

    This allows registration to occur without a single login; the device
    will be associated with a headless zone.
    """
    public_key = urllib.unquote(request.GET.get("device_key", ""))
    if RegisteredDevicePublicKey.objects.filter(public_key=public_key):
        return HttpResponseForbidden("Device is already registered.")

    # Create some zone.
    zone = Zone(name="Zone for public key %s" % public_key[:50])
    zone.save()

    # Add an association between a device 's public key and this zone,
    #   so that when registration is attempted by the distributed server
    #   with this key, it will register and receive this zone info.
    RegisteredDevicePublicKey(zone=zone, public_key=public_key).save()

    # Report success
    return JsonResponse({})
