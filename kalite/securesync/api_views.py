import re, json, uuid
from django.core import serializers
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
from main.models import VideoLog, ExerciseLog
from config.models import Settings

import crypto
import settings
from models import *


class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str) and not isinstance(content, unicode):
            content = simplejson.dumps(content, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)

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
        models = serializers.deserialize("json", data["client_device"])
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
        json_serializer.serialize(
            [Device.get_own_device(), registration.zone, device_zone], ensure_ascii=False
        )
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
             return JsonResponse({"error": "Client device matching id could not be found."}, status=500)
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
        "session": json_serializer.serialize([session], ensure_ascii=False),
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
    return JsonResponse({"devices": json_serializer.serialize(devices + devicezones, ensure_ascii=False)})

@csrf_exempt
@require_sync_session
def device_upload(data, session):
    # TODO(jamalex): check that the uploaded devices belong to the client device's zone and whatnot
    # (although it will only save zones from here if centrally signed, and devices if registered in a zone)
    result = save_serialized_models(data.get("devices", "[]"))
    session.models_uploaded += result["saved_model_count"]
    return JsonResponse(result)
        
@csrf_exempt
@gzip_page
@require_sync_session
def device_counters(data, session):
    device_counters = get_device_counters(session.client_device.get_zone())
    return JsonResponse({
        "device_counters": device_counters,
    })

@csrf_exempt
@require_sync_session
def upload_models(data, session):
    if "models" not in data:
        return JsonResponse({"error": "Must provide models."}, status=500)
    result = save_serialized_models(data["models"])
    session.models_uploaded += result["saved_model_count"]
    return JsonResponse(result)

@csrf_exempt
@gzip_page
@require_sync_session
def download_models(data, session):
    if "device_counters" not in data:
        return JsonResponse({"error": "Must provide device counters."}, status=500)
    result = get_serialized_models(data["device_counters"], zone=session.client_device.get_zone(), include_count=True)
    session.models_downloaded += result["count"]
    return JsonResponse({
        "models": result["models"]
    })
    
@csrf_exempt
def test_connection(request):
    return HttpResponse("OK")

def get_client_IP(request):
    from socket import gethostname, gethostbyname 
    ip = gethostbyname(gethostname()) 
    return 


def status(request):
    data = {
        "is_logged_in": request.is_logged_in,
        "registered": bool(Settings.get("registered")),
        "is_admin": request.is_admin,
        "is_django_user": request.is_django_user,
        "points": 0,
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
