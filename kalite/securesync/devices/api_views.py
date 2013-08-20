import cgi
import json
import re
import uuid

from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.core.urlresolvers import reverse
from django.db import models as db_models
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

import settings
import version
from .models import *
from shared import serializers
from utils.decorators import allow_jsonp, api_handle_error_with_json
from utils.internet import JsonResponse, am_i_online


@csrf_exempt
#@api_handle_error_with_json
def register_device(request):
    """Receives the client device info from the distributed server.
    Tries to register either because the device has been pre-registered,
    or because it has a valid INSTALL_CERTIFICATE."""
    # attempt to load the client device data from the request data
    data = simplejson.loads(request.raw_post_data or "{}")
    if "client_device" not in data:
        return JsonResponse({"error": "Serialized client device must be provided."}, status=500)
    try:
        # When hand-shaking on the device models, since we don't yet know the version,
        #   we have to just TRY with our own version.
        #
        # This is currently "central server" code, so
        #   this will only fail (currently) if the central server version
        #   is less than the version of a client--something that should never happen
        try:
            models = serializers.deserialize("json", data["client_device"], src_version=version.VERSION, dest_version=version.VERSION)
        except db_models.FieldDoesNotExist as fdne:
            raise Exception("Central server version is lower than client version.  This is ... impossible!")
        client_device = models.next().object
    except Exception as e:
        return JsonResponse({
            "error": "Could not decode the client device model: %r" % e,
            "code": "client_device_corrupted",
        }, status=500)

    # Validate the loaded data
    if not isinstance(client_device, Device):
        return JsonResponse({
            "error": "Client device must be an instance of the 'Device' model.",
            "code": "client_device_not_device",
        }, status=500)
    if not client_device.verify():
        return JsonResponse({
            "error": "Client device must be self-signed with a signature matching its own public key.",
            "code": "client_device_invalid_signature",
        }, status=500)

    #try:
    zone = register_self_registered_device(client_device, models)
#    except Exception as e:
#        return JsonResponse({
#            "error": "Failed to validate the chain of trust (%s)." % e,
#            "code": "chain_of_trust_invalid",
#        }, status=500)

    if not zone: # old code-path
        try:
            registration = RegisteredDevicePublicKey.objects.get(public_key=client_device.public_key)
            zone = registration.zone
            registration.delete()
        except RegisteredDevicePublicKey.DoesNotExist:
            try:
                device = Device.objects.get(public_key=client_device.public_key)
                return JsonResponse({
                    "error": "This device has already been registered",
                    "code": "device_already_registered",
                }, status=500)            
            except Device.DoesNotExist:
                return JsonResponse({
                    "error": "Device registration with public key not found; login and register first?",
                    "code": "public_key_unregistered",
                }, status=500)

    client_device.signed_by = client_device  # the device checks out; let's save it!
    client_device.save(imported=True)

    try:
        device_zone = DeviceZone(device=client_device, zone=zone)
        if not device_zone.get_existing_instance():
            device_zone.save()     # create the DeviceZone for the new device, with an 'upgraded' signature
    except Exception as e:
        pass#import pdb; pdb.set_trace()

    # return our local (server) Device, its Zone, and the newly created DeviceZone, to the client
    return JsonResponse(
        serializers.serialize("json", [Device.get_own_device(), zone, device_zone], dest_version=client_device.version, ensure_ascii=False)
    )


@transaction.commit_on_success
def register_self_registered_device(client_device, serialized_models):
    
    try:
        model_count = 0
        models = []
        for model in serialized_models:
            model_count += 1
            models.append(model.object)
            # HACK(bcipolli): DeviceZone fails to verify (for a few reasons),
            #   and I don't think making it requires_trusted_signature makes 
            #   sense.  For now, short-circuit the verify function--the
            #   verification is the ChainOfTrust verification below.
            model.object.save(imported=True)
            if model_count > 3 * ChainOfTrust.MAX_CHAIN_LENGTH:
                raise Exception("Chain of trust is too long.")

        # Now try to build a chain of from the device to the (claimed) zone
        client_zone = client_device.get_zone()
        if not client_zone.is_member(client_device):
            raise Exception("Chain of trust could not be established.")

        # If that works, then we just need to prove that the device has
        #   the private key of the ZoneInvitation.
        #

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
            device_info[field] = version.VERSION

        elif field == "video_count":
            from main.models import VideoFile
            device_info[field] = VideoFile.objects.filter(percent_complete=100).count() if not settings.CENTRAL_SERVER else 0

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
