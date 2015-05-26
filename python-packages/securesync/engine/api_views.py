import re

from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from .utils import get_serialized_models, save_serialized_models, get_device_counters, serialize
from .models import *
from ..devices.models import *  # inter-dependence
from fle_utils.chronograph.utils import force_job
from fle_utils.django_utils.functions import get_request_ip
from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError
from kalite.shared.decorators.auth import require_admin

def require_sync_session(handler):
    @api_handle_error_with_json
    def require_sync_session_wrapper_fn(request):
        if request.body:
            data = simplejson.loads(request.body)
        else:
            data = request.GET
        try:
            if "client_nonce" not in data:
                return JsonResponseMessageError("Client nonce must be specified.", status=400)
            session = SyncSession.objects.get(client_nonce=data["client_nonce"])
            if not session.verified:
                return JsonResponseMessageError("Session has not yet been verified.", status=401)
            if session.closed:
                return JsonResponseMessageError("Session is already closed.", status=401)
        except SyncSession.DoesNotExist:
            return JsonResponseMessageError("Session with specified client nonce could not be found.", status=403)
        response = handler(data, session)
        session.save()
        return response
    return require_sync_session_wrapper_fn


@csrf_exempt
@api_handle_error_with_json
def create_session(request):
    data = simplejson.loads(request.body or "{}")
    if "client_nonce" not in data:
        return JsonResponseMessageError("Client nonce must be specified.", status=400)
    if len(data["client_nonce"]) != 32 or re.match("[^0-9a-fA-F]", data["client_nonce"]):
        return JsonResponseMessageError("Client nonce is malformed (must be 32-digit hex).", status=400)
    if "client_device" not in data:
        return JsonResponseMessageError("Client device must be specified.", status=400)
    if "server_nonce" not in data:
        if SyncSession.objects.filter(client_nonce=data["client_nonce"]).count():
            return JsonResponseMessageError("Session already exists; include server nonce and signature.", status=401)
        session = SyncSession()
        session.client_nonce = data["client_nonce"]
        session.client_os = data.get("client_os", "")
        session.client_version = data.get("client_version", "")
        session.ip = get_request_ip(request)
        try:
            client_device = Device.objects.get(pk=data["client_device"])
            session.client_device = client_device
        except Device.DoesNotExist:
            # This is the codepath for unregistered devices trying to start a session.
            #   This would only get hit, however, if they manually run syncmodels.
            # But still, good to keep track of!
            UnregisteredDevicePing.record_ping(id=data["client_device"], ip=session.ip)
            return JsonResponseMessageError("Client device matching id could not be found. (id=%s)" % data["client_device"], status=400)

        session.server_nonce = uuid.uuid4().hex
        session.server_device = Device.get_own_device()
        if session.client_device.pk == session.server_device.pk:
            return JsonResponseMessageError("I know myself when I see myself, and you're not me.", status=401)
        session.save()
    else:
        try:
            session = SyncSession.objects.get(client_nonce=data["client_nonce"])
        except SyncSession.DoesNotExist:
            return JsonResponseMessageError("Session with specified client nonce could not be found.", status=401)
        if session.server_nonce != data["server_nonce"]:
            return JsonResponseMessageError("Server nonce did not match saved value.", status=401)
        if not data.get("signature", ""):
            return JsonResponseMessageError("Must include signature.", status=400)
        if not session.verify_client_signature(data["signature"]):
            return JsonResponseMessageError("Signature did not match.", status=401)
        session.verified = True
        session.save()

    # Return the serialized session, in the version intended for the other device
    return JsonResponse({
        "session": serialize([session], dest_version=session.client_version, ensure_ascii=False, sign=False, increment_counters=False ),
        "signature": session.sign(),
    })


@csrf_exempt
@require_sync_session
@api_handle_error_with_json
def destroy_session(data, session):
    session.closed = True
    return JsonResponse({})


@csrf_exempt
@gzip_page
@require_sync_session
@api_handle_error_with_json
def device_download(data, session):
    """This device is having its own devices downloaded"""
    zone = session.client_device.get_zone()
    devicezones = list(DeviceZone.all_objects.filter(zone=zone, device__in=data["devices"]))  # including deleted devicezones
    devices = [devicezone.device for devicezone in devicezones]
    session.models_downloaded += len(devices) + len(devicezones)

    # Return the objects serialized to the version of the other device.
    return JsonResponse({"devices": serialize(devices + devicezones, dest_version=session.client_version, ensure_ascii=False)})


@csrf_exempt
@require_sync_session
@api_handle_error_with_json
def device_upload(data, session):
    """This device is getting device-related objects from another device"""

    # TODO(jamalex): check that the uploaded devices belong to the client device's zone and whatnot
    # (although it will only save zones from here if centrally signed, and devices if registered in a zone)
    try:
        # Unserialize, knowing that the models were serialized by a client of its given version.
        #   dest_version assumed to be this device's version
        result = save_serialized_models(data.get("devices", "[]"), src_version=session.client_version)
    except Exception as e:
        logging.debug("Exception uploading devices (in api_views): %s" % e)
        result = { "error": e.message, "saved_model_count": 0 }

    session.models_uploaded += result["saved_model_count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@csrf_exempt
@gzip_page
@require_sync_session
@api_handle_error_with_json
def device_counters(data, session):

    device_counters = get_device_counters(zone=session.client_device.get_zone())
    return JsonResponse({
        "device_counters": device_counters,
    })


@csrf_exempt
@require_sync_session
@api_handle_error_with_json
def model_upload(data, session):
    """This device is getting data-related objects from another device."""

    if "models" not in data:
        return JsonResponseMessageError("Must provide models.", data={"saved_model_count": 0}, status=400)
    try:
        # Unserialize, knowing that the models were serialized by a client of its given version.
        #   dest_version assumed to be this device's version
        result = save_serialized_models(data["models"], src_version=session.client_version)
    except Exception as e:
        print "Exception uploading models (in api_views): %s, %s, %s" % (e.__class__.__name__, e.message, e.args)
        result = { "error": e.message, "saved_model_count": 0 }

    session.models_uploaded += result["saved_model_count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@csrf_exempt
@gzip_page
@require_sync_session
@api_handle_error_with_json
def model_download(data, session):
    """This device is having its own data downloaded"""

    if "device_counters" not in data:
        return JsonResponseMessageError("Must provide device counters.", data={"count": 0}, status=400)
    try:
        # Return the objects serialized to the version of the other device.
        result = get_serialized_models(data["device_counters"], zone=session.client_device.get_zone(), include_count=True, dest_version=session.client_version)
    except Exception as e:
        print "Exception downloading models (in api_views): %s, %s, %s" % (e.__class__.__name__, e.message, e.args)
        result = { "error": e.message, "count": 0 }

    session.models_downloaded += result["count"]
    session.errors += result.has_key("error")
    return JsonResponse(result)


@require_admin
@api_handle_error_with_json
def force_sync(request):
    """
    """
    force_job("syncmodels")  # now launches asynchronously
    return JsonResponse({})
