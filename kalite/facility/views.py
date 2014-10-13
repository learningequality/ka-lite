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
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, Http404
from django.shortcuts import get_object_or_404
from django.utils.html import strip_tags
from django.utils.translation import ugettext as _

from .decorators import facility_required, facility_from_request
from .forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from .middleware import refresh_session_facility_info
from .models import Facility, FacilityGroup, FacilityUser
from fle_utils.internet import set_query_params
from kalite.i18n import get_default_language
from kalite.main.models import UserLog
from student_testing.utils import set_exam_mode_off


from kalite.shared.decorators import require_authorized_admin
from securesync.devices.models import Zone
from securesync.devices.views import *



@require_authorized_admin
@render_to("facility/facility.html")
def facility_edit(request, id=None, zone_id=None):
    facil = (id != "new" and get_object_or_404(Facility, pk=id)) or None
    if facil:
        zone = facil.get_zone()
    else:
        zone = get_object_or_None(Zone, pk=zone_id)

    if settings.CENTRAL_SERVER:
        assert zone is not None

    if request.method != "POST":
        form = FacilityForm(instance=facil, initial={"zone_fallback": zone})
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


@require_authorized_admin
def add_facility_teacher(request):
    """
    Admins and coaches can add teachers
    If central, must be an org admin
    If distributed, must be superuser or a coach
    """
    title = _("Add a new teacher")
    return _facility_user(request, new_user=True, is_teacher=True, title=title)


@require_authorized_admin
def add_facility_student(request):
    """
    Admins and coaches can add students
    If central, must be an org admin
    If distributed, must be superuser or a coach
    """
    title = _("Add a new student")
    return _facility_user(request, new_user=True, title=title)


def facility_user_signup(request):
    """
    Anyone can sign up, unless we have set the restricted flag
    """
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("homepage"))

    if settings.DISABLE_SELF_ADMIN:
        # Users cannot create/edit their own data when UserRestricted
        raise PermissionDenied(_("Please contact a teacher or administrator to receive login information to this installation."))
    if settings.CENTRAL_SERVER:
        raise Http404(_("You may not sign up as a facility user on the central server."))

    title = _("Sign up for an account")
    return _facility_user(request, new_user=True, title=title)


@require_authorized_admin
def edit_facility_user(request, facility_user_id):
    """
    If users have permission to add a user, they also can edit the user. Additionally,
    a user may edit his/her own information, like in the case of a student.
    """
    user_being_edited = get_object_or_404(FacilityUser, id=facility_user_id) or None
    title = _("Edit user %(username)s") % {"username": user_being_edited.username}
    return _facility_user(request, user_being_edited=user_being_edited, is_teacher=user_being_edited.is_teacher, title=title)


@facility_required
@render_to("facility/facility_user.html")
def _facility_user(request, facility, title, is_teacher=False, new_user=False, user_being_edited=None):
    """
    Different codepaths for the following:
    * Django admin/teacher creates student (add_facility_student)
    * Django admin creates teacher
    * Django admin/edits a user, self, or student edits self (edit_facility_user)
    * Student creates self (facility_user_signup)

    Each has its own message and redirect.
    """
    next = request.next or request.get_full_path() or reverse("homepage")
    # Data submitted to create/edit the user.
    if request.method == "POST":

        form = FacilityUserForm(facility, data=request.POST, instance=user_being_edited)
        if not form.is_valid():
            messages.error(request, _("There was a problem saving the information provided; please review errors below."))

        else:
            # In case somebody tries to check the hidden 'is_teacher' field
            if form.cleaned_data["is_teacher"] and not request.is_admin:
                raise PermissionDenied(_("You must be a teacher to edit or create a teacher."))

            if form.cleaned_data["password_first"]:
                form.instance.set_password(form.cleaned_data["password_first"])

            form.save()

            # Editing self
            if request.session.get("facility_user") and request.session.get("facility_user").id == form.instance.id:
                messages.success(request, _("You successfully updated your user settings."))
                return HttpResponseRedirect(next)

            # Editing another user
            elif not new_user:
                messages.success(request, _("Changes saved for user '%(username)s'") % {"username": form.instance.get_name()})
                if request.next:
                    return HttpResponseRedirect(next)

            # New user created by admin
            elif request.is_admin:
                messages.success(request, _("You successfully created user '%(username)s'") % {"username": form.instance.get_name()})
                return HttpResponseRedirect(next)

            # New student signed up
            else:
                # Double check permissions
                messages.success(request, _("You successfully registered."))
                return HttpResponseRedirect(reverse("login"))

    # render form for editing
    elif user_being_edited:
        form = FacilityUserForm(facility=facility, instance=user_being_edited)

    # in all other cases, we are creating a new user
    else:
        form = FacilityUserForm(facility, initial={
            "group": request.GET.get("group", None),
            "is_teacher": is_teacher,
            "default_language": get_default_language(),
        })

    return {
        "title": title,
        "new_user": new_user,
        "form": form,
        "facility": facility,
        "teacher": is_teacher,
    }


@require_authorized_admin
@facility_required
@render_to("facility/facility_group.html")
def group_edit(request, facility, group_id):
    group = get_object_or_None(FacilityGroup, id=group_id)
    facility = facility or (group and group.facility)

    if request.method != 'POST':
        form = FacilityGroupForm(facility, instance=group)

    else:
        form = FacilityGroupForm(facility, data=request.POST, instance=group)
        if not form.is_valid():
            messages.error(request, _("Failed to save the group; please review errors below."))
        else:
            form.save()

            redir_url = request.next or request.GET.get("prev") or reverse("add_facility_student")
            redir_url = set_query_params(redir_url, {"facility": facility.pk, "group": form.instance.pk})
            return HttpResponseRedirect(redir_url)

    return {
        "form": form,
        "group_id": group_id,
        "facility": facility,
        "singlefacility": request.session["facility_count"] == 1,
        "title": _("Add a new group") if group_id == 'new' else _("Edit group"),
    }


@facility_from_request
@render_to("facility/login.html")
def login(request, facility):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse("homepage"))

    facility_id = (facility and facility.id) or None
    facilities = list(Facility.objects.all())

    #Fix for #2047: prompt user to create an admin account if none exists
    if not User.objects.exists():
        messages.warning(request, _("No administrator account detected. Please run 'python manage.py createsuperuser' from the terminal to create one."))

    # Fix for #1211: refresh cached facility info when it's free and relevant
    refresh_session_facility_info(request, facility_count=len(facilities))

    if request.method != 'POST':  # render the unbound login form
        referer = urlparse.urlparse(request.META["HTTP_REFERER"]).path if request.META.get("HTTP_REFERER") else None
        # never use the homepage as the referer
        if referer in [reverse("homepage"), reverse("add_facility_student"), reverse("add_facility_teacher"), reverse("facility_user_signup")]:
            referer = None
        form = LoginForm(initial={"facility": facility_id, "callback_url": referer})

    else:  # process the login form
        # log out any Django user or facility user
        logout(request)

        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # first try logging in as a Django user
        if not settings.CENTRAL_SERVER:
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
                if form.get_user().is_teacher:
                    landing_page = reverse("tabular_view")
                else:
                    landing_page = reverse("learn")

            return HttpResponseRedirect(request.next or landing_page)

    return {
        "form": form,
        "facilities": facilities,
        "sign_up_url": reverse("facility_user_signup"),
    }


def logout(request):
    # TODO(dylanjbarth) this is Nalanda specific
    if request.is_teacher:
        set_exam_mode_off()

    auth_logout(request)
    next = request.GET.get("next", reverse("homepage"))
    if next[0] != "/":
        next = "/"
    return HttpResponseRedirect(next)
