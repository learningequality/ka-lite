import re, json, uuid
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt

import crypto
import settings
from securesync.models import SyncSession, Device, RegisteredDevicePublicKey, json_serializer


class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str):
            content = simplejson.dumps(content, indent=2, cls=json.DjangoJSONEncoder, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


@csrf_exempt
def register_public_key(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    if "public_key" not in data:
        return JsonResponse({"error": "Public key must be specified."}, status=500)
    try:
        registration = RegisteredDevicePublicKey.objects.get(pk=data["public_key"])
    except RegisteredDevicePublicKey.DoesNotExist:
         return JsonResponse({"error": "Device registration with public key not found; "
            "login and register first?"}, status=500)
    client_device = Device()
    client_device.name = data.get("name", "New device")
    client_device.description = data.get("description", "")
    client_device.zone = registration.zone
    client_device.public_key = registration.public_key
    client_device.save()
    registration.delete()
    return JsonResponse(
        json_serializer.serialize([Device.get_own_device(), client_device], ensure_ascii=False, indent=2)
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
def destroy_session(request):
    
    return JsonResponse({
        "body": request.raw_post_data
    })
    
    
@csrf_exempt
def count_models(request):
    
    return JsonResponse({
        "body": request.raw_post_data
    })
    
    
@csrf_exempt 
def update_models(request):
    
    return JsonResponse({
        "body": request.raw_post_data
    })