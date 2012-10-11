import re, json, uuid
from django.core.serializers import json, serialize
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import condition
from annoying.decorators import render_to

import crypto
import settings
from securesync.models import SyncSession, Device


class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str):
            content = simplejson.dumps(content, indent=2, cls=json.DjangoJSONEncoder, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


@csrf_exempt
def create_session(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    if "client_nonce" not in data:
        return JsonResponse({"error": "Client nonce must be specified."}, status=500)
    if "client_device" not in data:
        return JsonResponse({"error": "Client device must be specified."}, status=500)
    if "server_nonce" not in data:
        session = SyncSession()
        session.client_nonce = data["client_nonce"]
        try:
            client_device = Device.objects.get(pk=data["client_device"])
            session.client_device = client_device
        except Device.DoesNotExist:
             return JsonResponse({"error": "Client device matching id could not be found."}, status=500)
        session.server_nonce = uuid.uuid4().hex
        session.server_device = Device.get_own_device()
        session.save()
    else:
        # try:
        session = SyncSession.objects.get(client_nonce=data["client_nonce"])
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