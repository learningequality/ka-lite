"""
"""
import cgi
import json
import re
import uuid
from annoying.functions import get_object_or_None

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.core.urlresolvers import reverse
from django.db import models as db_models
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

from .models import *
from .. import engine
from fle_utils.django_utils import get_request_ip
from fle_utils.internet import allow_jsonp, api_handle_error_with_json, am_i_online, JsonResponse, JsonResponseMessageError


@csrf_exempt
#@api_handle_error_with_json
def register_device(request):
    """Receives the client device info from the distributed server.
    Tries to register either because the device has been pre-registered,
    or because it has a valid INSTALL_CERTIFICATE."""
    # attempt to load the client device data from the request data
    data = simplejson.loads(request.body or "{}")
    if "client_device" not in data:
        return JsonResponseMessageError("Serialized client device must be provided.")
    try:
        # When hand-shaking on the device models, since we don't yet know the version,
        #   we have to just TRY with our own version.
        #
        # This is currently "central server" code, so
        #   this will only fail (currently) if the central server version
        #   is less than the version of a client--something that should never happen
        try:
            local_version = Device.get_own_device().get_version()
            models = engine.deserialize(data["client_device"], src_version=local_version, dest_version=local_version)
        except db_models.FieldDoesNotExist as fdne:
            raise Exception("Central server version is lower than client version.  This is ... impossible!")
        client_device = models.next().object
    except Exception as e:
        return JsonResponseMessageError("Could not decode the client device model: %s" % e, code="client_device_corrupted")

    # Validate the loaded data
    if not isinstance(client_device, Device):
        return JsonResponseMessageError("Client device must be an instance of the 'Device' model.", code="client_device_not_device")
    if not client_device.verify():
        return JsonResponseMessageError("Client device must be self-signed with a signature matching its own public key.", code="client_device_invalid_signature")

    try:
        zone = register_self_registered_device(client_device, models, data)
    except Exception as e:
        if e.args[0] == "Client not yet on zone.":
            zone = None
        else:
            # Client not on zone: allow fall-through via "old route"

            # This is the codepath for unregistered devices trying to start a session.
            #   This would only get hit, however, if they visit the registration page.
            # But still, good to keep track of!
            UnregisteredDevicePing.record_ping(id=client_device.id, ip=get_request_ip(request))

            return JsonResponseMessageError("Failed to validate the chain of trust (%s)." % e, code="chain_of_trust_invalid")

    if not zone: # old code-path
        try:
            registration = RegisteredDevicePublicKey.objects.get(public_key=client_device.public_key)
            if not registration.is_used():
                registration.use()

            elif get_object_or_None(Device, public_key=client_device.public_key):
                return JsonResponseMessageError("This device has already been registered", code="device_already_registered")
            else:
                # If not... we're in a very weird state--we have a record of their
                #   registration, but no device record.
                # Let's just let the registration happens, so we can refresh things here.
                #   No harm, and some failsafe benefit.
                # So, pass through... no code :)
                pass

            # Use the RegisteredDevicePublicKey, now that we've initialized the device and put it in its zone
            zone = registration.zone

        except RegisteredDevicePublicKey.DoesNotExist:
            try:
                device = Device.objects.get(public_key=client_device.public_key)
                return JsonResponseMessageError("This device has already been registered", code="device_already_registered")
            except Device.DoesNotExist:
                return JsonResponseMessageError("Device registration with public key not found; login and register first?", code="public_key_unregistered")

    client_device.save(imported=True)

    try:
        device_zone = DeviceZone.objects.get(device=client_device, zone=zone)
        device_zone.save()  # re-save, to give it a central server signature that will be honored by old clients
    except DeviceZone.DoesNotExist:
        device_zone = DeviceZone(device=client_device, zone=zone)
        device_zone.save()     # create the DeviceZone for the new device, with an 'upgraded' signature

    # return our local (server) Device, its Zone, and the newly created DeviceZone, to the client
    #   Note the order :)
    #
    # Addition: always back central server object--in case they didn't get it during install,
    #   they need it for software updating.
    return JsonResponse(
        engine.serialize([Device.get_central_server(), Device.get_own_device(), zone, device_zone], dest_version=client_device.version, ensure_ascii=False)
    )


@transaction.commit_on_success
def register_self_registered_device(client_device, serialized_models, request_data):

    try:
        model_count = 0
        for model in serialized_models:
            model.object.save(imported=True)

            model_count += 1
            if model_count > 3 * ChainOfTrust.MAX_CHAIN_LENGTH:
                raise Exception("Chain of trust is too long.")

        # Now try to build a chain of from the device to the (claimed) zone
        client_zone = client_device.get_zone()
        if not client_zone:
            raise Exception("Client not yet on zone.")
        elif not client_zone.is_member(client_device):
            raise Exception("Chain of trust could not be established.")

        # If that works, then we just need to prove that the device has
        #   the private key of the ZoneInvitation.
        #
        # This would be easy to do if we had a session; could just sign the nonce.
        #   However, we refuse to make a sync session if we don't know the device
        #   why?  Would it be better to make a session, then register within the session?
        # Let's talk.

        # we got through!  we got the zone, either recognized it or added it,
        #   and validated the certificate!
        return client_zone

    except StopIteration:
        # Old codepath has no objects here; signal to the outside that we've hit it
        return None


@csrf_exempt
@api_handle_error_with_json
def test_connection(request):
    return HttpResponse("OK")


@allow_jsonp
def get_server_info(request):
    """This function is used to check connection to central or local server and also to get specific data from server.

    Args:
        The http request.

    Returns:
        A json object containing general data from the server.

    """
    device = None
    zone = None

    device_info = {"status": "OK", "invalid_fields": []}

    for field in request.GET.get("fields", "").split(","):

        if field == "version":
            device = device or Device.get_own_device()
            device_info[field] = device.get_version()

        elif field == "device_name":
            device = device or Device.get_own_device()
            device_info[field] = device.name

        elif field == "device_description":
            device = device or Device.get_own_device()
            device_info[field] = device.description

        elif field == "device_description":
            device = device or Device.get_own_device()
            device_info[field] = device.description

        elif field == "device_id":
            device = device or Device.get_own_device()
            device_info[field] = device.id

        elif field == "zone_name":
            if settings.CENTRAL_SERVER:
                continue
            device = device or Device.get_own_device()
            zone = zone or device.get_zone()
            device_info[field] = zone.name if zone else None

        elif field == "zone_id":
            if settings.CENTRAL_SERVER:
                continue
            device = device or Device.get_own_device()
            zone = zone or device.get_zone()
            device_info[field] = zone.id if zone else None

        elif field == "online":
            if settings.CENTRAL_SERVER:
                device_info[field] =  True
            else:
                device_info[field] = am_i_online(url="%s://%s%s" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST, reverse("get_server_info")))

        elif field:
            # the field isn't one we know about, so add it to the list of invalid fields
            device_info["invalid_fields"].append(field)

    return JsonResponse(device_info)
