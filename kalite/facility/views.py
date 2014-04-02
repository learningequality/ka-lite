"""
"""
import urlparse
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

from .decorators import facility_required, facility_from_request
from .forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from .middleware import refresh_session_facility_info
from .models import Facility, FacilityGroup, FacilityUser
from fle_utils.chronograph import force_job
from fle_utils.internet import set_query_params
from kalite.i18n import get_default_language
from kalite.main.models import UserLog
from kalite.shared.decorators import require_admin
from securesync.devices.views import *


@require_admin
@render_to("facility/facility_edit.html")
def facility_edit(request, id=None):
    facil = (id != "new" and get_object_or_404(Facility, pk=id)) or None

    if request.method != "POST":
        form = FacilityForm(instance=facil)
    else:
        form = FacilityForm(data=request.POST, instance=facil)
        if not form.is_valid():
            messages.error(request, _("Failed to save the facility; please review errors below."))
        else:
            form.save()
            facil = form.instance
            # Translators: Do not change the text of '%(facility_name)s' because it is a variable, but you can change its position.
            messages.success(request, _("The facility '%(facility_name)s' has been successfully saved!") % {"facility_name": form.instance.name})
            return HttpResponseRedirect(request.next or reverse("zone_management", kwargs={"zone_id": getattr(facil.get_zone(), "id", "None")}))

    return {
        "form": form
    }


@require_admin
def add_facility_teacher(request):
    return edit_facility_user(request, id="new", is_teacher=True)


def add_facility_student(request):
    return edit_facility_user(request, id="new", is_teacher=False)


@facility_required
@render_to("facility/facility_user.html")
def edit_facility_user(request, facility, is_teacher=None, id=None):
    """Different codepaths for the following:
    * Django admin/teacher creates user, teacher
    * Student creates self

    Each has its own message and redirect.
    """

    title = ""
    user = (id != "new" and get_object_or_404(FacilityUser, id=id)) or None

    # Check permissions
    if user and not request.is_admin and user != request.session.get("facility_user"):
        # Editing a user, user being edited is not self, and logged in user is not admin
        raise PermissionDenied()

    elif settings.DISABLE_SELF_ADMIN and not request.is_admin:
        # Users cannot create/edit their own data when UserRestricted
        raise PermissionDenied(_("Please contact a teacher or administrator to receive login information to this installation."))

    # Data submitted to create the user.
    if request.method == "POST":  # now, teachers and students can belong to a group, so all use the same form.

        form = FacilityUserForm(facility, data=request.POST, instance=user)
        if not form.is_valid():
            messages.error(request, _("There was a problem saving the information provided; please review errors below."))

        else:
            if form.cleaned_data["password_first"]:
                form.instance.set_password(form.cleaned_data["password_first"])
            form.save()

            if getattr(request.session.get("facility_user"), "id", None) == form.instance.id:
                # Edited: own account; refresh the facility_user setting
                request.session["facility_user"] = form.instance
                messages.success(request, _("You successfully updated your user settings."))
                return HttpResponseRedirect(request.next or reverse("account_management"))

            elif id != "new":
                # Edited: by admin; someone else's ID
                messages.success(request, _("User changes saved for user '%s'") % form.instance.get_name())
                if request.next:
                    return HttpResponseRedirect(request.next)

            elif request.is_admin:
                # Created: by admin
                messages.success(request, _("You successfully created user '%s'") % form.instance.get_name())
                return HttpResponseRedirect(request.next or request.get_full_path() or reverse("homepage"))  # allow them to add more of the same thing.

            else:
                # Created: by self
                messages.success(request, _("You successfully registered."))
                return HttpResponseRedirect(request.next or "%s?facility=%s" % (reverse("login"), form.data["facility"]))

    # For GET requests
    elif user:
        form = FacilityUserForm(facility=facility, instance=user)
        title = _("Edit user") + " " + user.username
        is_teacher = user.is_teacher

    else:
        assert is_teacher is not None, "Must call this function with is_teacher set."
        form = FacilityUserForm(facility, initial={
            "group": request.GET.get("group", None),
            "is_teacher": is_teacher,
            "default_language": get_default_language()
        })

    if not title:
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
@render_to("facility/add_facility.html")
def add_facility(request):

    if request.method != "POST":
        form = FacilityForm()
    else:
        form = FacilityForm(data=request.POST)
        if not form.is_valid():
            messages.error(request, _("Failed to save the facility; please review errors below."))
        else:
            form.save()
            return HttpResponseRedirect(reverse("add_facility_student") + "?facility=" + form.instance.pk)

    return {
        "form": form
    }


@require_admin
@facility_required
@render_to("facility/add_group.html")
def add_group(request, facility):
    groups = FacilityGroup.objects.all()

    if request.method != 'POST':
        form = FacilityGroupForm()

    else:
        form = FacilityGroupForm(data=request.POST)
        if not form.is_valid():
            messages.error(request, _("Failed to save the facility; please review errors below."))
        else:
            form.instance.facility = facility
            form.save()

            redir_url = request.next or request.GET.get("prev") or reverse("add_facility_student")
            redir_url = set_query_params(redir_url, {"facility": facility.pk, "group": form.instance.pk})
            return HttpResponseRedirect(redir_url)

    return {
        "form": form,
        "facility": facility,
        "groups": groups,
        "singlefacility": request.session["facility_count"] == 1,
    }


@facility_from_request
@render_to("facility/login.html")
def login(request, facility):
    facility_id = (facility and facility.id) or None
    facilities = list(Facility.objects.all())

    # Fix for #1211: refresh cached facility info when it's free and relevant
    refresh_session_facility_info(request, facility_count=len(facilities))

    if request.method != 'POST':  # render the unbound login form
        referer = urlparse.urlparse(request.META["HTTP_REFERER"]).path if request.META.get("HTTP_REFERER") else None
        # never use the homepage as the referer
        if referer in [reverse("homepage"), reverse("add_facility_student")]:
            referer = None
        form = LoginForm(initial={"facility": facility_id, "callback_url": referer})

    else:  # process the login form
        # log out any Django user or facility user
        logout(request)

        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # first try logging in as a Django user
        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            return HttpResponseRedirect(request.next or reverse("zone_redirect"))

        # try logging in as a facility user
        form = LoginForm(data=request.POST, request=request, initial={"facility": facility_id})
        if not form.is_valid():
            messages.error(
                request,
                _("There was an error logging you in. Please correct any errors listed below, and try again."),
            )

        else:
            user = form.get_user()

            try:
                UserLog.begin_user_activity(user, activity_type="login", language=request.language)  # Success! Log the event (ignoring validation failures)
            except ValidationError as e:
                logging.error("Failed to begin_user_activity upon login: %s" % e)

            request.session["facility_user"] = user
            messages.success(request, _("You've been logged in! We hope you enjoy your time with KA Lite ") +
                                        _("-- be sure to log out when you finish."))

            # Send them back from whence they came
            landing_page = form.cleaned_data["callback_url"]
            if not landing_page:
                # Just going back to the homepage?  We can do better than that.
                landing_page = reverse("coach_reports") if form.get_user().is_teacher else None
                landing_page = landing_page or (reverse("account_management") if False else reverse("homepage"))  # TODO: pass the redirect as a parameter.

            return HttpResponseRedirect(form.non_field_errors() or request.next or landing_page)

    return {
        "form": form,
        "facilities": facilities,
        "sign_up_url": reverse("add_facility_student"),
    }


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
