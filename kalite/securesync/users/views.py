from __future__ import absolute_import

import urllib
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

import settings
from config.models import Settings
from main.models import UserLog
from securesync.forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from securesync.models import Facility, FacilityGroup
from settings import LOG as logging
from shared.decorators import require_admin, central_server_only, distributed_server_only, facility_required, facility_from_request
from shared.jobs import force_job
from utils.internet import set_query_params


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
                messages.error(
                    request,
                    _("To continue, you must first add a facility (e.g. for your school). ")
                    + _("Please use the form below to add a facility."))
            else:
                messages.error(
                    request,
                    _("You must first have the administrator of this server log in below to add a facility.")
                )
            redir_url = reverse("add_facility")
            redir_url = set_query_params(redir_url, {"prev": request.META.get("HTTP_REFERER", "")})
            return HttpResponseRedirect(redir_url)

        else:
            facility = get_facility_from_request(request)
        if facility:
            return handler(request, facility, *args, **kwargs)
        else:
            return facility_selection(request)

    return inner_fn


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


@distributed_server_only
@render_to("securesync/add_facility_user.html")
@facility_required
def add_facility_user(request, facility, is_teacher):
    """Different codepaths for the following:
    * Django admin/teacher creates user, teacher
    * Student creates self

    Each has its own message and redirect.
    """

    # Data submitted to create the user.
    if request.method == "POST":  # now, teachers and students can belong to a group, so all use the same form.
        form = FacilityUserForm(request, data=request.POST, initial={"facility": facility})
        if form.is_valid():
            form.instance.set_password(form.cleaned_data["password"])
            form.instance.is_teacher = is_teacher
            form.save()

            # Admins create users while logged in.
            if request.is_logged_in:
                assert request.is_admin, "Regular users can't create users while logged in."
                messages.success(request, _("You successfully created the user."))
                return HttpResponseRedirect(request.META.get("PATH_INFO", reverse("homepage")))  # allow them to add more of the same thing.
            else:
                messages.success(request, _("You successfully registered."))
                return HttpResponseRedirect("%s?facility=%s" % (reverse("login"), form.data["facility"]))

    # For GET requests
    else:
        form = FacilityUserForm(
            request,
            initial={
                "facility": facility,
                "group": request.GET.get("group", None)
            }
        )

    # Across POST and GET requests
    form.fields["group"].queryset = FacilityGroup.objects.filter(facility=facility)

    return {
        "form": form,
        "facility": facility,
        "singlefacility": (Facility.objects.count() == 1),
        "teacher": is_teacher,
        "cur_url": request.path,
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
    groups = FacilityGroup.objects.all()
    if request.method == 'POST' and request.is_admin:
        form = FacilityGroupForm(data=request.POST)
        if form.is_valid():
            form.instance.facility = facility
            form.save()

            redir_url = request.GET.get("prev") or reverse("add_facility_student")
            redir_url = set_query_params(redir_url, {"facility": facility.pk, "group": form.instance.pk})
            return HttpResponseRedirect(redir_url)

    elif request.method == 'POST' and not request.is_admin:
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
@facility_from_request
@render_to("securesync/login.html")
def login(request, facility):
    facilities = Facility.objects.all()
    facility_id = facility and facility.id or None

    if request.method == 'POST':
        # log out any Django user or facility user
        logout(request)

        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # first try logging in as a Django user
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            return HttpResponseRedirect(request.next or reverse("easy_admin"))

        # try logging in as a facility user
        form = LoginForm(data=request.POST, request=request, initial={"facility": facility_id})
        if form.is_valid():
            user = form.get_user()

            try:
                UserLog.begin_user_activity(user, activity_type="login")  # Success! Log the event (ignoring validation failures)
            except ValidationError as e:
                logging.debug("Failed to begin_user_activity upon login: %s" % e)
            request.session["facility_user"] = user
            messages.success(request, _("You've been logged in! We hope you enjoy your time with KA Lite ") +
                                        _("-- be sure to log out when you finish."))
            return HttpResponseRedirect(
                form.non_field_errors()
                or request.next
                or reverse("coach_reports") if form.get_user().is_teacher else reverse("student_view")
            )
        else:
            messages.error(
                request,
                strip_tags(form.non_field_errors())
                or _("There was an error logging you in. Please correct any errors listed below, and try again.")
            )

    else:  # render the unbound login form
        form = LoginForm(initial={"facility": facility_id})

    return {
        "form": form,
        "facilities": facilities
    }


@distributed_server_only
def logout(request):
    if "facility_user" in request.session:
        # Logout, ignore any errors.
        try:
            UserLog.end_user_activity(request.session["facility_user"], activity_type="login")
        except ValidationError as e:
            logging.debug("Failed to end_user_activity upon logout: %s" % e)
        del request.session["facility_user"]
    auth_logout(request)
    next = request.GET.get("next", reverse("homepage"))
    if next[0] != "/":
        next = "/"
    return HttpResponseRedirect(next)

