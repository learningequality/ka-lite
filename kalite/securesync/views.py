import re, json, uuid
from django.core.serializers import json, serialize
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.utils import simplejson
from annoying.decorators import render_to
from forms import RegisteredDevicePublicKeyForm

import crypto
import settings
from securesync.models import SyncSession, Device, RegisteredDevicePublicKey, Zone

@render_to("securesync/register.html")
def register(request):
    form = RegisteredDevicePublicKeyForm(request.user)
    
    return {
        "form": form
    }


# @render_to("securesync/edit_organization.html")
# def edit_organization(request):
#     if request.method == 'POST':
#         form = OrganizationForm(data=request.POST)
#         if form.is_valid():
        
        
#     else:
