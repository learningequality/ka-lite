import urllib
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

import settings
from .forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from .models import Facility, FacilityGroup
from config.models import Settings
from main.models import UserLog
from securesync.devices.views import *
from securesync.forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from securesync.models import Facility, FacilityGroup, FacilityUser
from settings import LOG as logging
from shared.decorators import require_admin, central_server_only, distributed_server_only, facility_required, facility_from_request
from shared.jobs import force_job
from utils.internet import set_query_params


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
@require_admin
def add_facility_teacher(request):
    return edit_facility_user(request, id="new", is_teacher=True)


@distributed_server_only
def add_facility_student(request):
    return edit_facility_user(request, id="new", is_teacher=False)


@distributed_server_only
@render_to("securesync/add_facility_user.html")
@facility_required
def edit_facility_user(request, facility, is_teacher=None, id=None):
    """Different codepaths for the following:
    * Django admin/teacher creates user, teacher
    * Student creates self

    Each has its own message and redirect.
    """

    user = get_object_or_404(FacilityUser, id=id) if id != "new" else None
    title = ""

    # Data submitted to create the user.
    if request.method == "POST":  # now, teachers and students can belong to a group, so all use the same form.
        if not request.is_admin and settings.package_selected("UserRestricted"):
            raise PermissionDenied(_("Please contact a teacher or administrator to receive login information to this installation."))

        form = FacilityUserForm(facility, data=request.POST, instance=user)
        if form.is_valid():
            if form.cleaned_data["password"]:
                form.instance.set_password(form.cleaned_data["password"])
            form.save()

            # Admins create users while logged in.
            if id == "new":
                if request.is_logged_in:
                    assert request.is_admin, "Regular users can't create users while logged in."
                    messages.success(request, _("You successfully created the user."))
                    return HttpResponseRedirect(request.META.get("PATH_INFO", reverse("homepage")))  # allow them to add more of the same thing.
                else:
                    messages.success(request, _("You successfully registered."))
                    return HttpResponseRedirect("%s?facility=%s" % (reverse("login"), form.data["facility"]))
            else:
                messages.success(request, _("User changes saved!"))
                if request.next:
                    return HttpResponseRedirect(request.next)

    # For GET requests
    elif user:
        form = FacilityUserForm(facility=facility, instance=user)
        title = _("Edit user") + " " + user.username

    else:
        assert is_teacher is not None, "Must call this function with is_teacher set."
        form = FacilityUserForm(facility, initial={
            "group": request.GET.get("group", None),
            "is_teacher": is_teacher,
        })
        if not request.is_admin:
            title = _("Sign up for an account")
        elif is_teacher:
            title = _("Add a new teacher")
        else:
            title = _("Add a new student")

    return {
        "title": title,
        "user_id": id,
        "form": form,
        "facility": facility,
        "singlefacility": request.session["facility_count"] == 1,
        "num_groups": form.fields["group"].choices.queryset.count(),
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
        "groups": groups,
        "singlefacility": request.session["facility_count"] == 1,
    }


@distributed_server_only
@facility_from_request
@render_to("securesync/login.html")
def login(request, facility):
    facilities = list(Facility.objects.all())
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
                UserLog.begin_user_activity(user, activity_type="login", language=request.language)  # Success! Log the event (ignoring validation failures)
            except ValidationError as e:
                logging.error("Failed to begin_user_activity upon login: %s" % e)
            request.session["facility_user"] = user
            messages.success(request, _("You've been logged in! We hope you enjoy your time with KA Lite ") +
                                        _("-- be sure to log out when you finish."))
            landing_page = reverse("coach_reports") if form.get_user().is_teacher else None
            landing_page = landing_page or (reverse("account_management") if not settings.package_selected("RPi") else reverse("homepage"))

            return HttpResponseRedirect(form.non_field_errors() or request.next or landing_page)
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
        "facilities": facilities,
    }


@distributed_server_only
def logout(request):
    if "facility_user" in request.session:
        # Logout, ignore any errors.
        try:
            UserLog.end_user_activity(request.session["facility_user"], activity_type="login")
        except ValidationError as e:
            logging.error("Failed to end_user_activity upon logout: %s" % e)
        del request.session["facility_user"]

    auth_logout(request)
    next = request.GET.get("next", reverse("homepage"))
    if next[0] != "/":
        next = "/"
    return HttpResponseRedirect(next)

