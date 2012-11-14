import re, json, uuid, urllib
from django.contrib.auth.decorators import login_required
from django.core.serializers import json, serialize
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.utils import simplejson
from annoying.decorators import render_to
from forms import RegisteredDevicePublicKeyForm, FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout      

import crypto
import settings
from securesync.models import SyncSession, Device, RegisteredDevicePublicKey, Zone, Facility, FacilityGroup
from securesync.api_client import SyncClient

def require_admin(handler):
    def wrapper_fn(request, *args, **kwargs):
        if not request.is_admin:
            return HttpResponseRedirect(reverse("login") + "?next=" + request.path)
        return handler(request, *args, **kwargs)
    return wrapper_fn

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

def register_public_key(request):
    if settings.CENTRAL_SERVER:
        return register_public_key_server(request)
    else:
        return register_public_key_client(request)

@require_admin
@render_to("securesync/register_public_key_client.html")
def register_public_key_client(request):
    if Device.get_own_device().get_zone():
        return {"already_registered": True}
    client = SyncClient()
    if client.test_connection() != "success":
        return {"no_internet": True}
    reg_status = client.register()
    if reg_status == "registered":
        return {"newly_registered": True}
    if reg_status == "device_already_registered":
        return {"already_registered": True}
    if reg_status == "public_key_unregistered":
        return {
            "unregistered": True,
            "registration_url": client.path_to_url(
                "/securesync/register/?" + urllib.quote(crypto.serialize_public_key())),
        }
    return HttpResponse("Registration status: " + reg_status)

@central_server_only
@login_required
@render_to("securesync/register_public_key_server.html")
def register_public_key_server(request):
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
@render_to("securesync/select_facility_to_add_user.html")
def select_facility_to_add_user(request):
    facilities = Facility.objects.all()
    context = {"facilities": facilities}
    return context
    
@distributed_server_only
@render_to("securesync/add_facility_user.html")
def add_facility_user(request, id):
    if request.method == "POST":
        form = FacilityUserForm(request, data=request.POST)
        if form.is_valid():
            form.instance.set_password(form.cleaned_data["password"])
            form.save()
            return HttpResponseRedirect(reverse("login"))
    elif Facility.objects.count() == 0 or id is None:
        messages.error(request, "You must add a facility before creating a user" )
        return HttpResponseRedirect(reverse("add_facility"))
    else:
        form = FacilityUserForm(request, initial={'facility':id})
    facility = Facility.objects.get(pk=id)
    form.fields["group"].queryset = FacilityGroup.objects.filter(facility=id)
    if Facility.objects.count() == 1:
        singlefacility = True
    else:
        singlefacility = False
    return {
        "form": form,
        "facility": facility,
        "singlefacility": singlefacility,
    }

@require_admin
@render_to("securesync/add_facility.html")
def add_facility(request):
    if request.method == 'POST' and request.is_admin:
        form = FacilityForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("select_facility_to_add_user"))
    elif request.method =='POST' and not request.is_admin:
        messages.error(request,"Just what do you think you're doing, Dave?")
        return HttpResponseRedirect(reverse("login"))
    else:
        form = FacilityForm()
    return {
        "form": form
    }

@require_admin
@render_to("securesync/add_group.html")
def add_group(request, id):
    facilities = Facility.objects.all()
    groups = FacilityGroup.objects.all()
    if request.method == 'POST' and request.is_admin:
        form = FacilityGroupForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_facility_user", kwargs={"id": id}))
    elif request.method =='POST' and not request.is_admin:
        messages.error(request,"This mission is too important for me to allow you to jeopardize it.")
        return HttpResponseRedirect(reverse("login"))
    else:
        form = FacilityGroupForm(initial={'facility':id})
    return {
        "form": form,
        "facility_id": id,
        "facilities": facilities,
        "groups": groups
    }


@distributed_server_only
@render_to("securesync/login.html")
def login(request):
    if request.user.is_authenticated():
        auth_logout(request)
    if request.method == 'POST':
        if "facility_user" in request.session:
            del request.session["facility_user"]
        next = request.GET.get("next", "/")
        if next[0] != "/":
            next = "/"
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            return HttpResponseRedirect(next)
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            request.session["facility_user"] = form.get_user()
            return HttpResponseRedirect(next)
    else:
        form = LoginForm()
    return {
        "form": form
    }

@distributed_server_only
def logout(request):
    if "facility_user" in request.session:
        del request.session["facility_user"]
    auth_logout(request)
    next = request.GET.get("next", "/")
    if next[0] != "/":
        next = "/"
    return HttpResponseRedirect(next)

# @render_to("securesync/edit_organization.html")
# def edit_organization(request):
#     if request.method == 'POST':
#         form = OrganizationForm(data=request.POST)
#         if form.is_valid():
        
        
#     else:
