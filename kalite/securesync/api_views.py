import cgi
import json
import re
import uuid

from django.core import serializers
from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

import settings
import version
from config.models import Settings
from main.models import VideoLog, ExerciseLog
from securesync import crypto, model_sync
from securesync.models import *
from utils.decorators import distributed_server_only
from utils.internet import JsonResponse


def require_sync_session(handler):
    def wrapper_fn(request):
        if request.raw_post_data:
            data = simplejson.loads(request.raw_post_data)
        else:
            data = request.GET
        try:
            if "client_nonce" not in data:
                return JsonResponse({"error": "Client nonce must be specified."}, status=500)
            session = SyncSession.objects.get(client_nonce=data["client_nonce"])
            if not session.verified:
                return JsonResponse({"error": "Session has not yet been verified."}, status=500)
            if session.closed:
                return JsonResponse({"error": "Session is already closed."}, status=500)
        except SyncSession.DoesNotExist:
            return JsonResponse({"error": "Session with specified client nonce could not be found."}, status=500)
        response = handler(data, session)
        session.save()
        return response
    return wrapper_fn


@csrf_exempt
def register_device(request):
    data = simplejson.loads(request.raw_post_data or "{}")

    # attempt to load the client device data from the request data
    if "client_device" not in data:
        return JsonResponse({"error": "Serialized client device must be provided."}, status=500)
    try:
        models = serializers.deserialize("json", data["client_device"], client_version=None, server_version=version.VERSION)
        client_device = models.next().object
    except Exception as e:
        return JsonResponse({
            "error": "Could not decode the client device model: %r" % e,
            "code": "client_device_corrupted",
        }, status=500)
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

    # we have a valid self-signed Device, so now check if its public key has been registered
    try:
        registration = RegisteredDevicePublicKey.objects.get(public_key=client_device.public_key)
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

    client_device.signed_by = client_device

    # the device checks out; let's save it!
    client_device.save(imported=True)

    # create the DeviceZone for the new device
    device_zone = DeviceZone(device=client_device, zone=registration.zone)
    device_zone.save()

    # delete the RegisteredDevicePublicKey, now that we've initialized the device and put it in its zone
    registration.delete()

    # return our local (server) Device, its Zone, and the newly created DeviceZone, to the client
    return JsonResponse(
        serializers.serialize("json", [Device.get_own_device(), registration.zone, device_zone], client_version=client_device.version, ensure_ascii=False)
    )


@csrf_exempt
def create_session(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    if "client_nonce" not in data:
        return JsonResponse({"error": "Client nonce must be specified."}, status=500)
    if len(data["client_nonce"]) != 32 or re.match("[^0-9a-fA-F]", data["client_nonce"]):
        return JsonResponse({"error": "Client nonce is malformed (must be 32-digit hex)."}, status=500)
    if "client_device" not in data:
        return JsonResponse({"error": "Client device must be specified."}, status=500)
    if "server_nonce" not in data:
        if SyncSession.objects.filter(client_nonce=data["client_nonce"]).count():
            return JsonResponse({"error": "Session already exists; include server nonce and signature."}, status=500)
        session = SyncSession()
        session.client_nonce = data["client_nonce"]
        session.client_os = data.get("client_os", "")
        session.client_version = data.get("client_version", "")
        try:
            client_device = Device.objects.get(pk=data["client_device"])
            session.client_device = client_device
        except Device.DoesNotExist:
            return JsonResponse({"error": "Client device matching id could not be found. (id=%s)" % data["client_device"]}, status=500)
        session.server_nonce = uuid.uuid4().hex
        session.server_device = Device.get_own_device()
        session.ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get('REMOTE_ADDR', ""))
        if session.client_device.pk == session.server_device.pk:
            return JsonResponse({"error": "I know myself when I see myself, and you're not me."}, status=500)
        session.save()
    else:
        try:
            session = SyncSession.objects.get(client_nonce=data["client_nonce"])
        except SyncSession.DoesNotExist:
            return JsonResponse({"error": "Session with specified client nonce could not be found."}, status=500)
        if session.server_nonce != data["server_nonce"]:
            return JsonResponse({"error": "Server nonce did not match saved value."}, status=500)
        if not data.get("signature", ""):
            return JsonResponse({"error": "Must include signature."}, status=500)
        if not session.verify_client_signature(data["signature"]):
            return JsonResponse({"error": "Signature did not match."}, status=500)
        session.verified = True
        session.save()

    return JsonResponse({
        "session": serializers.serialize("json", [session], client_version=session.client_version, ensure_ascii=False ),
        "signature": session.sign(),
    })


@csrf_exempt
@require_sync_session
def destroy_session(data, session):
    session.closed = True
    return JsonResponse({})


@csrf_exempt
@gzip_page
@require_sync_session
def device_download(data, session):
    zone = session.client_device.get_zone()
    devicezones = list(DeviceZone.objects.filter(zone=zone, device__in=data["devices"]))
    devices = [devicezone.device for devicezone in devicezones]
    session.models_downloaded += len(devices) + len(devicezones)
    return JsonResponse({"devices": serializers.serialize("json", devices + devicezones, client_version=session.client_version, ensure_ascii=False)})


@csrf_exempt
@require_sync_session
def device_upload(data, session):
    # TODO(jamalex): check that the uploaded devices belong to the client device's zone and whatnot
    # (although it will only save zones from here if centrally signed, and devices if registered in a zone)
    try:
        result = model_sync.save_serialized_models(data.get("devices", "[]"), client_version=session.client_version)
    except Exception as e:
        result = { "error": e.message, "saved_model_count": 0 }
        
    session.models_uploaded += result["saved_model_count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@csrf_exempt
@gzip_page
@require_sync_session
def device_counters(data, session):
    device_counters = Device.get_device_counters(session.client_device.get_zone())
    return JsonResponse({
        "device_counters": device_counters,
    })


@csrf_exempt
@require_sync_session
def model_upload(data, session):
    if "models" not in data:
        return JsonResponse({"error": "Must provide models.", "saved_model_count": 0}, status=500)
    try:
        result = model_sync.save_serialized_models(data["models"], client_version=session.client_version)
    except Exception as e:
        result = { "error": e.message, "saved_model_count": 0 }

    session.models_uploaded += result["saved_model_count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@csrf_exempt
@gzip_page
@require_sync_session
def model_download(data, session):
    if "device_counters" not in data:
        return JsonResponse({"error": "Must provide device counters.", "count": 0}, status=500)
    try:
        result = model_sync.get_serialized_models(data["device_counters"], zone=session.client_device.get_zone(), include_count=True, client_version=session.client_version)
    except Exception as e:
        result = { "error": e.message, "count": 0 }

    session.models_downloaded += result["count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@csrf_exempt
def test_connection(request):
    return HttpResponse("OK")


# On pages with no forms, we want to ensure that the CSRF cookie is set, so that AJAX POST
# requests will be possible. Since `status` is always loaded, it's a good place for this.
@ensure_csrf_cookie
@distributed_server_only
def status(request):
    """In order to promote (efficient) caching on (low-powered)
    distributed devices, we do not include ANY user data in our
    templates.  Instead, an AJAX request is made to download user
    data, and javascript used to update the page.

    This view is the view providing the json blob of user information,
    for each page view on the distributed server.

    Besides basic user data, we also provide access to the
    Django message system through this API, again to promote
    caching by excluding any dynamic information from the server-generated
    templates.
    """
    # Build a list of messages to pass to the user.
    #   Iterating over the messages removes them from the
    #   session storage, thus they only appear once.
    message_dicts = []
    for message in get_messages(request):
        # Make sure to escape strings not marked as safe.
        # Note: this duplicates a bit of Django template logic.
        msg_txt = message.message
        if not (isinstance(message.message, SafeString) or isinstance(message.message, SafeUnicode)):
            msg_txt = cgi.escape(str(msg_txt))

        message_dicts.append({
            "tags": message.tags,
            "text": msg_txt,
        })

    data = {
        "is_logged_in": request.is_logged_in,
        "registered": bool(Settings.get("registered")),
        "is_admin": request.is_admin,
        "is_django_user": request.is_django_user,
        "points": 0,
        "messages": message_dicts,
    }
    if "facility_user" in request.session:
        user = request.session["facility_user"]
        data["is_logged_in"] = True
        data["username"] = user.get_name()
        data["points"] = VideoLog.get_points_for_user(user) + ExerciseLog.get_points_for_user(user)
    if request.user.is_authenticated():
        data["is_logged_in"] = True
        data["username"] = request.user.username

    return JsonResponse(data)
