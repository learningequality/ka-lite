import re, json, uuid
from django.core import serializers
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt

import crypto
import settings
from models import SyncSession, Device, DeviceZone, RegisteredDevicePublicKey, json_serializer, get_device_counters, save_serialized_models


class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str):
            content = simplejson.dumps(content, indent=2, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)

def require_sync_session(handler):
    def wrapper_fn(request):
        data = simplejson.loads(request.raw_post_data or "{}")
        try:
            session = SyncSession.objects.get(client_nonce=data["client_nonce"])
        except SyncSession.DoesNotExist:
            return JsonResponse({"error": "Session with specified client nonce could not be found."}, status=500)
        return handler(data, session)
    return wrapper_fn

@csrf_exempt
def register_device(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    
    # attempt to load the client device data from the request data
    if "client_device" not in data:
        return JsonResponse({"error": "Serialized client device must be provided."}, status=500)
    try:
        models = serializers.deserialize("json", data["client_device"])
        client_device = models[0].object
    except:
        return JsonResponse({
            "error": "Could not decode the client device model; corrupted?",
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
        registration = RegisteredDevicePublicKey.objects.get(pk=client_device.public_key)
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
    
    # the device checks out; let's save it!
    client_device.save()
    
    # create the DeviceZone for the new device
    device_zone = DeviceZone(device=client_device, zone=registration.zone)
    device_zone.save()
    
    # delete the RegisteredDevicePublicKey, now that we've initialized the device and put it in its zone
    registration.delete()
    
    # return our local (server) Device, its Zone, and the newly created DeviceZone, to the client
    return JsonResponse(
        json_serializer.serialize(
            [Device.get_own_device(), registration.zone, device_zone], ensure_ascii=False, indent=2
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
        try:
            client_device = Device.objects.get(pk=data["client_device"])
            session.client_device = client_device
        except Device.DoesNotExist:
             return JsonResponse({"error": "Client device matching id could not be found."}, status=500)
        session.server_nonce = uuid.uuid4().hex
        session.server_device = Device.get_own_device()
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
        "client_nonce": session.client_nonce,
        "client_device": session.client_device.pk,
        "server_nonce": session.server_nonce,
        "server_device": session.server_device.pk,
        "verified": session.verified,
        "signature": session.sign(),
    })
    
@csrf_exempt
@require_sync_session
def destroy_session(data, session):
    session.delete()
    return JsonResponse({})
    
@csrf_exempt
@require_sync_session
def device_counters(data, session):
    if "device_counters" not in data:
        return JsonResponse({"error": "Must provide device counters."}, status=500)
    client_counters = data["device_counters"]
    server_counters = get_device_counters(session.client_device.get_zone())
    counters_to_request = {}
    counters_to_send = {}
    for device in client_counters:
        if client_counters[device] > server_counters.get(device, 0):
            counters_to_request[device] = server_counters.get(device, 0) + 1
    for device in server_counters:
        if server_counters[device] > client_counters.get(device, 0):
            counters_to_send[device] = client_counters.get(device, 0) + 1
    return JsonResponse({
        "device_counters": counters_to_request,
        "models": get_serialized_models(counters_to_send, limit=data.get("limit", 100))
    })

@csrf_exempt
@require_sync_session
def update_models(data, session):
    if "models" not in data:
        return JsonResponse({"error": "Must provide device counters."}, status=500)
    save_serialized_models(data["models"])
    return JsonResponse({})
    
@csrf_exempt
def test_connection(request):
    return HttpResponse("OK")


def status(request):
    data = {
        "logged_in": False,
        "registered": Device.get_own_device() and True or False,
    }
    if "facility_user" in request.session:
        user = request.session["facility_user"]
        data["logged_in"] = True
        data["username"] = user.get_name()
    return JsonResponse(data)
