import urlparse
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

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

import settings
from .decorators import facility_required, facility_from_request
from .forms import FacilityUserForm, LoginForm, FacilityForm, FacilityGroupForm
from .middleware import refresh_session_facility_info
from .models import Facility, FacilityGroup, FacilityUser
from chronograph import force_job
from main.models import UserLog
from securesync.devices.views import *
from settings import LOG as logging
from shared.decorators import require_admin
from testing.asserts import central_server_only, distributed_server_only
from utils.internet import set_query_params

@require_admin
@distributed_server_only
@render_to("facility/facility_admin.html")
def facility_admin(request):
    facilities = Facility.objects.all()
    context = {"facilities": facilities}
    return context


@require_admin
@distributed_server_only
@render_to("facility/facility_edit.html")
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
@facility_required
@render_to("facility/facility_user.html")
def edit_facility_user(request, facility, is_teacher=None, id=None):
    """Different codepaths for the following:
    * Django admin/teacher creates user, teacher
    * Student creates self

    Each has its own message and redirect.
    """

    title = ""
    user = get_object_or_404(FacilityUser, id=id) if id != "new" else None

    # Check permissions
    if user and not request.is_admin and user != request.session.get("facility_user"):
        # Editing a user, user being edited is not self, and logged in user is not admin
        raise PermissionDenied()
    elif settings.package_selected("UserRestricted") and not request.is_admin:
        # Users cannot create/edit their own data when UserRestricted
        raise PermissionDenied(_("Please contact a teacher or administrator to receive login information to this installation."))

    # Data submitted to create the user.
    if request.method == "POST":  # now, teachers and students can belong to a group, so all use the same form.

        form = FacilityUserForm(facility, data=request.POST, instance=user)
        if form.is_valid():
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
                return HttpResponseRedirect(request.META.get("PATH_INFO", request.next or reverse("homepage")))  # allow them to add more of the same thing.

            else:
                # Created: by self
                messages.success(request, _("You successfully registered."))
                return HttpResponseRedirect(request.next or "%s?facility=%s" % (reverse("login"), form.data["facility"]))

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
@render_to("facility/add_group.html")
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
@render_to("facility/login.html")
def login(request, facility):
    facility_id = facility and facility.id or None
    facilities = list(Facility.objects.all())

    # Fix for #1211: refresh cached facility info when it's free and relevant
    refresh_session_facility_info(request, facility_count=len(facilities))

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

            # Send them back from whence they came
            landing_page = form.cleaned_data["callback_url"]
            if not landing_page:
                # Just going back to the homepage?  We can do better than that.
                landing_page = reverse("coach_reports") if form.get_user().is_teacher else None
                landing_page = landing_page or (reverse("account_management") if not settings.package_selected("RPi") else reverse("homepage"))

            return HttpResponseRedirect(form.non_field_errors() or request.next or landing_page)

        else:
            messages.error(
                request,
                _("There was an error logging you in. Please correct any errors listed below, and try again."),
            )

    else:  # render the unbound login form
        referer = urlparse.urlparse(request.META["HTTP_REFERER"]).path if request.META.get("HTTP_REFERER") else None
        # never use the homepage as the referer
        if referer in [reverse("homepage"), reverse("add_facility_student")]:
            referer = None
        form = LoginForm(initial={"facility": facility_id, "callback_url": referer})

    return {
        "form": form,
        "facilities": facilities,
        "sign_up_url": reverse("add_facility_student"),
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


@require_admin
@facility_required
@render_to("facility/current_users.html")
def user_list(request, facility):

    # Use default group
    group_id = request.REQUEST.get("group_id")
    if not group_id:
        groups = FacilityGroup.objects \
            .annotate(models.Count("facilityuser")) \
            .filter(facilityuser__count__gt=0)
        ngroups = groups.count()
        ngroups += int(FacilityUser.objects.filter(group__isnull=True).count() > 0)
        if ngroups == 1:
            group_id = groups[0].id if groups.count() else "Ungrouped"

    context = user_management_context(
        request=request,
        facility_id=facility.id,
        group_id=group_id,
        page=request.REQUEST.get("page","1"),
    )
    context.update({
        "singlefacility": Facility.objects.count() == 1,
    })
    return context


def user_management_context(request, facility_id, group_id, page=1, per_page=25):
    facility = get_object_or_None(Facility, id=facility_id)
    groups = FacilityGroup.objects \
        .filter(facility=facility) \
        .order_by("name")

    # This could be moved into a function shared across files, if necessary.
    #   For now, moving into function, as outside if function it looks more
    #   general-purpose than it's being used / tested now.
    def get_users_from_group(group_id, facility=None):
        if _(group_id) == _("Ungrouped"):
            return list(FacilityUser.objects \
                .filter(facility=facility, group__isnull=True) \
                .order_by("last_name", "first_name", "username"))
        elif not group_id:
            return []
        else:
            return list(get_object_or_404(FacilityGroup, pk=group_id) \
                .facilityuser_set \
                .order_by("last_name", "first_name", "username"))

    user_list = get_users_from_group(group_id, facility=facility)

    # Get the user list from the group
    if not user_list:
        users = []
    else:
        paginator = Paginator(user_list, per_page)
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

    if users:
        if users.has_previous():
            prevGETParam = request.GET.copy()
            prevGETParam["page"] = users.previous_page_number()
            previous_page_url = "?" + prevGETParam.urlencode()
        else:
            previous_page_url = ""
        if users.has_next():
            nextGETParam = request.GET.copy()
            nextGETParam["page"] = users.next_page_number()
            next_page_url = "?" + nextGETParam.urlencode()
        else:
            next_page_url = ""
    context = {
        "facility": facility,
        "users": users,
        "groups": groups,
        "group_id": group_id,
        "facility_id": facility_id,
        "ungrouped": _("Ungrouped"),
    }
    if users:
        context["pageurls"] = {"next_page": next_page_url, "prev_page": previous_page_url}
    return context