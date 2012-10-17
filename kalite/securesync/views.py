import re, json, uuid
from django.contrib.auth.decorators import login_required
from django.core.serializers import json, serialize
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.utils import simplejson
from annoying.decorators import render_to
from forms import RegisteredDevicePublicKeyForm, FacilityUserForm, LoginForm

import crypto
import settings
from securesync.models import SyncSession, Device, RegisteredDevicePublicKey, Zone

def central_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            return HttpResponseNotFound("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn

def distributed_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            return HttpResponseNotFound("This path is only available on distributed servers.")
        return handler(*args, **kwargs)
    return wrapper_fn

@central_server_only
@login_required
@render_to("securesync/register_device.html")
def register_device(request):
    if request.method == 'POST':
        form = RegisteredDevicePublicKeyForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("homepage"))
    else:
        form = RegisteredDevicePublicKeyForm(request.user)
    return {
        "form": form
    }

@distributed_server_only
@render_to("securesync/add_facility_user.html")
def add_facility_user(request):
    if request.method == 'POST':
        form = FacilityUserForm(data=request.POST)
        if form.is_valid():
            form.instance.set_password(form.cleaned_data["password"])
            form.save()
            return HttpResponseRedirect(reverse("login"))
    else:
        form = FacilityUserForm()
    return {
        "form": form
    }

@distributed_server_only
@render_to("securesync/login.html")
def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            request.session["facility_user"] = form.get_user()
            return HttpResponseRedirect("/")
    else:
        form = LoginForm()
    return {
        "form": form
    }

@distributed_server_only
def logout(request):
    if "facility_user" in request.session:
        del request.session["facility_user"]
    return HttpResponseRedirect("/")

# @render_to("securesync/edit_organization.html")
# def edit_organization(request):
#     if request.method == 'POST':
#         form = OrganizationForm(data=request.POST)
#         if form.is_valid():
        
        
#     else:
