"""
"""
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from securesync.devices.views import *  # ARGH! TODO(aron): figure out what things are imported here, and import them specifically

from django import forms
from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from .decorators import facility_required
from .forms import FacilityUserForm, FacilityGroupForm
from .models import Facility, FacilityGroup, FacilityUser
from fle_utils.internet.functions import set_query_params
from kalite.dynamic_assets.decorators import dynamic_settings
from kalite.i18n import get_default_language
from kalite.shared.decorators.auth import require_authorized_admin


@require_authorized_admin
def add_facility_teacher(request):
    """
    Admins and coaches can add teachers
    If central, must be an org admin
    If distributed, must be superuser or a coach
    """
    title = _("Add a new coach")
    return _facility_user(request, new_user=True, is_teacher=True, title=title)


@require_authorized_admin
@dynamic_settings
def add_facility_student(request, ds):
    """
    Admins and coaches can add students
    If central, must be an org admin
    If distributed, must be superuser or a coach
    """
    if request.is_teacher and not ds["facility"].teacher_can_create_students:
        return HttpResponseForbidden()

    title = _("Add a new learner")
    return _facility_user(request, new_user=True, title=title)


def facility_user_signup(request):
    """
    Anyone can sign up, unless we have set the restricted flag
    """
    if getattr(request, "is_logged_in", False):
        return HttpResponseRedirect(reverse("homepage"))

    if settings.DISABLE_SELF_ADMIN:
        # Users cannot create/edit their own data when UserRestricted
        raise PermissionDenied(_("Please contact a coach or administrator to receive login information to this installation."))
    if settings.CENTRAL_SERVER:
        raise Http404(_("You may not sign up as a facility user on the central server."))

    title = _("Sign up for an account")
    return _facility_user(request, new_user=True, title=title)


@require_authorized_admin
@dynamic_settings
def edit_facility_user(request, ds, facility_user_id):
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
            elif request.is_admin or request.is_django_user:
                messages.success(request, _("You successfully created user '%(username)s'") % {"username": form.instance.get_name()})
                if request.next:
                    return HttpResponseRedirect(next)
                else:
                    zone_id = getattr(facility.get_zone(), "id", None)
                    return HttpResponseRedirect(reverse("facility_management", kwargs={"zone_id": zone_id, "facility_id": facility.id}))

            # New student signed up
            else:
                # Double check permissions
                messages.success(request, _("You successfully registered."))
                return HttpResponseRedirect(reverse("homepage"))

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

    if is_teacher or (not (request.is_admin or request.is_teacher) and FacilityGroup.objects.filter(facility=facility).count() == 0) or (not new_user and not (request.is_admin or request.is_teacher)):
        form.fields['group'].widget = forms.HiddenInput()
    if Facility.objects.count() < 2 or (not new_user and not request.is_admin):
        form.fields['facility'].widget = forms.HiddenInput()

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

