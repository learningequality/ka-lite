import re, json, uuid, urllib
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers import json, serialize
from django.core.urlresolvers import reverse
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.html import strip_tags
from annoying.decorators import render_to
from forms import RegisteredDevicePublicKeyForm, FacilityUserForm, FacilityTeacherForm, LoginForm, FacilityForm, FacilityGroupForm
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout   
from annoying.functions import get_object_or_None   
from config.models import Settings

import crypto
import settings
from securesync.models import SyncSession, Device, RegisteredDevicePublicKey, Zone, Facility, FacilityGroup
from securesync.api_client import SyncClient
from utils.jobs import force_job
from utils.decorators import require_admin

from django.utils.translation import ugettext as _

def central_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if not settings.CENTRAL_SERVER:
            return HttpResponseNotFound("This path is only available on the central server.")
        return handler(*args, **kwargs)
    return wrapper_fn


def distributed_server_only(handler):
    def wrapper_fn(*args, **kwargs):
        if settings.CENTRAL_SERVER:
            return HttpResponseNotFound(_("This path is only available on distributed servers."))
        return handler(*args, **kwargs)
    return wrapper_fn


def register_public_key(request):
    if settings.CENTRAL_SERVER:
        return register_public_key_server(request)
    else:
        return register_public_key_client(request)


def get_facility_from_request(request):
    if "facility" in request.GET:
        facility = get_object_or_None(Facility, pk=request.GET["facility"])
        if "set_default" in request.GET and request.is_admin and facility:
            Settings.set("default_facility", facility.id)
    elif "facility_user" in request.session:
        facility = request.session["facility_user"].facility
    elif Facility.objects.count() == 1:
        facility = Facility.objects.all()[0]
    else:
        facility = get_object_or_None(Facility, pk=Settings.get("default_facility"))
    return facility


def facility_required(handler):
    def inner_fn(request, *args, **kwargs):
        
        if Facility.objects.count() == 0:
            if request.is_admin:
                messages.error(request, _("To continue, you must first add a facility (e.g. for your school). ") \
                    + _("Please use the form below to add a facility."))
            else:
                messages.error(request,
                    _("You must first have the administrator of this server log in below to add a facility."))
            return HttpResponseRedirect(reverse("add_facility"))
        else:
            facility = get_facility_from_request(request)
        
        if facility:
            return handler(request, facility, *args, **kwargs)
        else:
            return facility_selection(request)
    
    return inner_fn


def set_as_registered():
    force_job("syncmodels", "Secure Sync", "HOURLY")
    Settings.set("registered", True)


@require_admin
@render_to("securesync/register_public_key_client.html")
def register_public_key_client(request):
    import pdb; pdb.set_trace()
    if Device.get_own_device().get_zone():
        set_as_registered()   
        return {"already_registered": True}
    client = SyncClient()
    if client.test_connection() != "success":
        return {"no_internet": True}
    reg_response = client.register()
    reg_status = reg_response.get("code")
    if reg_status == "registered":
        set_as_registered()
        return {"newly_registered": True}
    if reg_status == "device_already_registered":
        set_as_registered()
        return {"already_registered": True}
    if reg_status == "public_key_unregistered":
        return {
            "unregistered": True,
            "registration_url": client.path_to_url(
                "/securesync/register/?" + urllib.quote(crypto.get_own_key().get_public_key_string())),
            "login_url": client.path_to_url("/accounts/login/")
        }
    error_msg = reg_response.get("error", "")
    if error_msg:
        return {"error_msg": error_msg}
    return HttpResponse(_("Registration status: ") + reg_status)

@central_server_only
@login_required
@render_to("securesync/register_public_key_server.html")
def register_public_key_server(request):
    if request.method == 'POST':
        form = RegisteredDevicePublicKeyForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("The device's public key has been successfully registered. You may now close this window."))
            return HttpResponseRedirect(reverse("homepage"))
    else:
        form = RegisteredDevicePublicKeyForm(request.user)
    return {
        "form": form
    }


@require_admin
@distributed_server_only
@render_to("securesync/facility_admin.html")
def facility_admin(request):
    facilities = Facility.objects.all()
    context = {"facilities": facilities}
    return context


@require_admin
@distributed_server_only
@render_to("securesync/facility_edit.html")
def facility_edit(request, id=None):
    if id != "new":
        facil = get_object_or_404(Facility, pk=id)
    else:
        facil = None
    if request.method == "POST":
        form = FacilityForm(data=request.POST, instance=facil)
        if form.is_valid():
            form.save()
            # Translators: Do not change the text of '%(facility_name)s' because it is a variable, but you can change its position. 
            messages.success(request, _("The facility '%(facility_name)s' has been successfully saved!") % {"facility_name": form.instance.name})
            return HttpResponseRedirect(request.next or reverse("facility_admin"))
    else:
        form = FacilityForm(instance=facil)
    return {
        "form": form
    }


@distributed_server_only
@render_to("securesync/facility_selection.html")
def facility_selection(request):
    facilities = Facility.objects.all()
    context = {"facilities": facilities}
    return context


@distributed_server_only
@require_admin
def add_facility_teacher(request):
    return add_facility_user(request, is_teacher=True)


@distributed_server_only
def add_facility_student(request):
    return add_facility_user(request, is_teacher=False)


@render_to("securesync/add_facility_user.html")
@facility_required
def add_facility_user(request, facility, is_teacher):
    if is_teacher:
        Form = FacilityTeacherForm
    else:
        Form = FacilityUserForm
    if request.method == "POST":
        form = Form(request, data=request.POST, initial={"facility": facility})
        if form.is_valid():
            form.instance.set_password(form.cleaned_data["password"])
            form.instance.is_teacher = is_teacher
            form.save()
            if request.is_logged_in:
                return HttpResponseRedirect(reverse("homepage"))
            else:
                return HttpResponseRedirect(reverse("login") + "?facility=" + facility.pk)
    elif Facility.objects.count() == 0:
        messages.error(request, _("You must add a facility before creating a user"))
        return HttpResponseRedirect(reverse("add_facility"))
    else:
        if is_teacher:
            form = Form(request, initial={"facility": facility})
        else:
            form = Form(request, initial={"facility": facility, "group": request.GET.get("group", None)})
    if not is_teacher:
        form.fields["group"].queryset = FacilityGroup.objects.filter(facility=facility)
    if Facility.objects.count() == 1:
        singlefacility = True
    else:
        singlefacility = False
    return {
        "form": form,
        "facility": facility,
        "singlefacility": singlefacility,
        "teacher": is_teacher,
    }


@require_admin
@render_to("securesync/add_facility.html")
def add_facility(request):
    if request.method == "POST":
        form = FacilityForm(data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_facility_student") + "?facility=" + form.instance.pk)
    else:
        form = FacilityForm()
    return {
        "form": form
    }


@require_admin
@facility_required
@render_to("securesync/add_group.html")
def add_group(request, facility):
    facilities = Facility.objects.all()
    groups = FacilityGroup.objects.all()
    if request.method == 'POST' and request.is_admin:
        form = FacilityGroupForm(data=request.POST)
        if form.is_valid():
            form.instance.facility = facility
            form.save()
            return HttpResponseRedirect(reverse("add_facility_student") + "?facility=" + facility.pk + "&group=" + form.instance.pk)
    elif request.method =='POST' and not request.is_admin:
        messages.error(request, _("This mission is too important for me to allow you to jeopardize it."))
        return HttpResponseRedirect(reverse("login"))
    else:
        form = FacilityGroupForm()
    return {
        "form": form,
        "facility": facility,
        "groups": groups
    }


@distributed_server_only
@render_to("securesync/login.html")
def login(request):
    facilities = Facility.objects.all()
    
    facility = get_facility_from_request(request)
    facility_id = facility and facility.id or None
    
    if request.method == 'POST':
        
        # log out any Django user
        if request.user.is_authenticated():
            auth_logout(request)
        
        # log out a facility user
        if "facility_user" in request.session:
            del request.session["facility_user"]
        
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        
        # first try logging in as a Django user
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            return HttpResponseRedirect(request.next or "/")
        
        # try logging in as a facility user
        form = LoginForm(data=request.POST, request=request, initial={"facility": facility_id})
        if form.is_valid():
            request.session["facility_user"] = form.get_user()
            messages.success(request, _("You've been logged in! We hope you enjoy your time with KA Lite ") +
                                        _("-- be sure to log out when you finish."))
            return HttpResponseRedirect(form.non_field_errors() or request.next or "/")
        else:
            messages.error(request, strip_tags(form.non_field_errors()) or
                _("There was an error logging you in. Please correct any errors listed below, and try again."))
        
    else: # render the unbound login form
        form = LoginForm(initial={"facility": facility_id})
    
    return {
        "form": form,
        "facilities": facilities
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


@distributed_server_only
def crypto_login(request):
    if "client_nonce" in request.GET:
        client_nonce = request.GET["client_nonce"]
        try:
            session = SyncSession.objects.get(client_nonce=client_nonce)
        except SyncSession.DoesNotExist:
            return HttpResponseServerError("Session not found.")
        if session.server_device.get_metadata().is_trusted:
            user = get_object_or_None(User, username="centraladmin")
            if not user:
                user = User(username="centraladmin", is_superuser=True, is_staff=True, is_active=True)
                user.set_unusable_password()
                user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            auth_login(request, user)
        session.delete()
    return HttpResponseRedirect("/")
