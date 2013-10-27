import datetime
from annoying.decorators import render_to, wraps
from annoying.functions import get_object_or_None
from collections import OrderedDict, namedtuple

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

import settings
from .forms import ZoneForm, UploadFileForm
try:
    from central.models import Organization
except:
    from django.db import models
    class Organization(models.Model):
        pass
from coachreports.views import student_view_context
from main import topicdata
from main.models import ExerciseLog, VideoLog, UserLog, UserLogSummary
from securesync.forms import FacilityForm
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device, Zone, SyncSession
from settings import LOG as logging
from shared.decorators import require_authorized_admin, require_authorized_access_to_student_data
from utils.internet import CsvResponse, render_to_csv


@require_authorized_admin
@render_to("control_panel/zone_form.html")
def zone_form(request, zone_id, org_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_404(Zone, pk=zone_id) if zone_id != "new" else None

    if request.method == "POST":
        form = ZoneForm(data=request.POST, instance=zone)
        if form.is_valid():
            form.instance.save()
            if org:
                org.zones.add(form.instance)
            if zone_id == "new":
                zone_id = form.instance.pk
            return HttpResponseRedirect(reverse("zone_management", kwargs={ "org_id": org_id, "zone_id": zone_id }))
    else:
        form = ZoneForm(instance=zone)
    return {
        "org": org,
        "zone": zone,
        "form": form,
    }


@require_authorized_admin
@render_to("control_panel/zone_management.html")
def zone_management(request, zone_id, org_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_404(Zone, pk=zone_id)# if zone_id != "new" else None
    own_device = Device.get_own_device()

    # Accumulate device data
    device_data = OrderedDict()
    for device in Device.objects.filter(devicezone__zone=zone).order_by("devicemetadata__is_demo_device", "name"):

        user_activity = UserLogSummary.objects.filter(device=device)
        sync_sessions = SyncSession.objects.filter(client_device=device)
        if not settings.CENTRAL_SERVER and device.id != own_device.id:  # Non-local sync sessions unavailable on distributed server
            sync_sessions = None

        exercise_activity = ExerciseLog.objects.filter(signed_by=device)

        device_data[device.id] = {
            "name": device.name or device.id,
            "is_demo_device": device.devicemetadata.is_demo_device,
            "num_times_synced": sync_sessions.count() if sync_sessions is not None else None,
            "last_time_synced": sync_sessions.aggregate(Max("timestamp"))["timestamp__max"] if sync_sessions is not None else None,
            "is_demo_device": device.get_metadata().is_demo_device,
            "last_time_used":   exercise_activity.order_by("-completion_timestamp")[0:1] if user_activity.count() == 0 else user_activity.order_by("-end_datetime")[0],
            "counter": device.get_counter_position(),
        }

    # Accumulate facility data
    facility_data = OrderedDict()
    for facility in Facility.objects.by_zone(zone).order_by("name"):

        user_activity = UserLogSummary.objects.filter(user__facility=facility)
        exercise_activity = ExerciseLog.objects.filter(user__facility=facility)

        facility_data[facility.id] = {
            "name": facility.name,
            "num_users":  FacilityUser.objects.filter(facility=facility).count(),
            "num_groups": FacilityGroup.objects.filter(facility=facility).count(),
            "id": facility.id,
            "last_time_used":   exercise_activity.order_by("-completion_timestamp")[0:1] if user_activity.count() == 0 else user_activity.order_by("-end_datetime")[0],
        }

    return {
        "org": org,
        "zone": zone,
        "facilities": facility_data,
        "devices": device_data,
        "upload_form": UploadFileForm(),
        "own_device_is_trusted": Device.get_own_device().get_metadata().is_trusted,
    }


@require_authorized_admin
def delete_zone(request, org_id, zone_id):
    zone = Zone.objects.get(pk=zone_id)
    if not zone.has_dependencies(passable_classes=["Organization"]):
        zone.delete()
        messages.success(request, "You have successfully deleted " + zone.name + ".")
    else:
        messages.warning(request, "You cannot delete this zone because it is syncing data with with %d device(s)" % zone.devicezone_set.count())
    return HttpResponseRedirect(reverse("org_management"))

#TODO(bcipolli) I think this will be deleted on the central server side
@require_authorized_admin
@render_to("control_panel/facility_management.html")
def facility_management(request, zone_id, org_id=None):
    facilities = Facility.objects.by_zone(zone_id)
    return {
        "zone_id": zone_id,
        "facilities": facilities,
    }


@require_authorized_admin
@render_to("control_panel/facility_usage.html")
@render_to_csv(["students", "teachers"], key_label="user_id", order="stacked")
def facility_usage(request, facility_id, org_id=None, zone_id=None, frequency=None):

    # Basic data
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facility = get_object_or_404(Facility, pk=facility_id)
    groups = FacilityGroup.objects.filter(facility=facility).order_by("name")
    students = FacilityUser.objects \
        .filter(facility=facility, is_teacher=False) \
        .order_by("last_name", "first_name", "username") \
        .prefetch_related("group")
    teachers = FacilityUser.objects \
        .filter(facility=facility, is_teacher=True) \
        .order_by("last_name", "first_name", "username") \
        .prefetch_related("group")
    
    # Get the start and end date--based on csv.  A hack, yes...
    if request.GET.get("format", "") == "csv":
        frequency = frequency or request.GET.get("fequency", "months")
        (period_start, period_end) = _get_date_range(frequency)
    else:
        (period_start, period_end) = (None, None)

    (student_data, group_data) = _get_user_usage_data(students, period_start=period_start, period_end=period_end)
    (teacher_data, _) = _get_user_usage_data(teachers, period_start=period_start, period_end=period_end)

    # Total hack for CSV-only
    if request.GET.get("format") == "csv":
        (period_start, period_end) = _get_date_range(frequency)
    else:
        period_start = None
        period_end = None

    return {
        "org": org,
        "zone": zone,
        "facility": facility,
        "groups": group_data,
        "students": student_data,
        "teachers": teacher_data,
        "date_range": [period_start, period_end] if frequency else [None, None],
    }



def _get_date_range(frequency):
    """
    Hack function (while CSV is in initial stages),
        returns dates of beginning and end of last month.
    Should be extended to do something more generic, based on
    "frequency", and moved into utils/general.py
    """
    assert frequency == "months"

    if frequency == "months":  # only works for months ATM
        cur_date = datetime.datetime.now()
        first_this_month = datetime.datetime(year=cur_date.year, month=cur_date.month, day=1, hour=0, minute=0, second=0)
        period_end = first_this_month - datetime.timedelta(seconds=1)
        period_start = datetime.datetime(year=period_end.year, month=period_end.month, day=1)
    return (period_start, period_end)


def _get_user_usage_data(users, period_start=None, period_end=None):
    """
    Returns facility user data, within the given date range.
    """

    # compute period start and end
    # Now compute stats, based on queried data
    len_all_exercises = len(topicdata.NODE_CACHE['Exercise'])
    user_data = OrderedDict()
    group_data = OrderedDict()


    # Make queries efficiently
    exercise_logs = ExerciseLog.objects.filter(user__in=users, complete=True)
    video_logs = VideoLog.objects.filter(user__in=users)
    login_logs = UserLogSummary.objects.filter(user__in=users)

    # filter results
    if period_start:
        exercise_logs = exercise_logs.filter(completion_timestamp__gte=period_start)
        video_logs = video_logs.filter(completion_timestamp__gte=period_start)
        login_logs = login_logs.filter(start_datetime__gte=period_start)
    if period_end:
        exercise_logs = exercise_logs.filter(completion_timestamp__lte=period_end)
        video_logs = video_logs.filter(completion_timestamp__lte=period_end)
        login_logs = login_logs.filter(end_datetime__lte=period_end)

    # Force results in a single query
    exercise_logs = list(exercise_logs.values("exercise_id", "user__pk"))
    video_logs = list(video_logs.values("youtube_id", "user__pk"))
    login_logs = list(login_logs.values("activity_type", "total_seconds", "user__pk"))

    for user in users:
        user_data[user.pk] = OrderedDict()
        user_data[user.pk]["first_name"] = user.first_name
        user_data[user.pk]["last_name"] = user.last_name
        user_data[user.pk]["username"] = user.username
        user_data[user.pk]["group"] = user.group


        user_data[user.pk]["total_report_views"] = 0#report_stats["count__sum"] or 0
        user_data[user.pk]["total_logins"] =0# login_stats["count__sum"] or 0
        user_data[user.pk]["total_hours"] = 0#login_stats["total_seconds__sum"] or 0)/3600.

        user_data[user.pk]["total_exercises"] = 0
        user_data[user.pk]["pct_mastery"] = 0.
        user_data[user.pk]["exercises_mastered"] = []

        user_data[user.pk]["total_videos"] = 0
        user_data[user.pk]["videos_watched"] = []
    

    for elog in exercise_logs:
        user_data[elog["user__pk"]]["total_exercises"] += 1
        user_data[elog["user__pk"]]["pct_mastery"] += 1. / len_all_exercises
        user_data[elog["user__pk"]]["exercises_mastered"].append(elog["exercise_id"])

    for vlog in video_logs:
        user_data[vlog["user__pk"]]["total_videos"] += 1
        user_data[vlog["user__pk"]]["videos_watched"].append(vlog["youtube_id"])

    for llog in login_logs:
        if llog["activity_type"] == UserLog.get_activity_int("coachreport"):
            user_data[llog["user__pk"]]["total_report_views"] += 1
        elif llog["activity_type"] == UserLog.get_activity_int("login"):
            user_data[llog["user__pk"]]["total_hours"] += (llog["total_seconds"]) / 3600.
            user_data[llog["user__pk"]]["total_logins"] += 1

    # Add group data.  Allow a fake group "Ungrouped"
    for user in users:
        group_pk = getattr(user.group, "pk", None)
        group_name = getattr(user.group, "name", "Ungrouped")
        if not group_pk in group_data:
            group_data[group_pk] = {
                "name": group_name,
                "total_logins": 0,
                "total_hours": 0,
                "total_users": 0,
                "total_videos": 0,
                "total_exercises": 0,
                "pct_mastery": 0,
            }
        group_data[group_pk]["total_users"] += 1
        group_data[group_pk]["total_logins"] += user_data[user.pk]["total_logins"]
        group_data[group_pk]["total_hours"] += user_data[user.pk]["total_hours"]
        group_data[group_pk]["total_videos"] += user_data[user.pk]["total_videos"]
        group_data[group_pk]["total_exercises"] += user_data[user.pk]["total_exercises"]

        total_mastery_so_far = (group_data[group_pk]["pct_mastery"] * (group_data[group_pk]["total_users"] - 1) + user_data[user.pk]["pct_mastery"])
        group_data[group_pk]["pct_mastery"] =  total_mastery_so_far / group_data[group_pk]["total_users"]

    return (user_data, group_data)


@require_authorized_admin
@render_to("control_panel/device_management.html")
def device_management(request, device_id, org_id=None, zone_id=None, n_sessions=10):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    device = get_object_or_404(Device, pk=device_id)

    sync_sessions = SyncSession.objects \
        .filter(client_device=device) \
        .order_by("-timestamp")

    return {
        "org": org,
        "zone": zone,
        "device": device,
        "sync_sessions": sync_sessions[:n_sessions],
        "total_sessions": sync_sessions.count(), 
        "n_sessions": min(sync_sessions.count(), n_sessions),
    }


@require_authorized_admin
@render_to("control_panel/facility_form.html")
def facility_form(request, facility_id, org_id=None, zone_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facil = get_object_or_404(Facility, pk=facility_id) if id != "new" else None

    if request.method != "POST":
        form = FacilityForm(instance=facil)

    else:
        form = FacilityForm(data=request.POST, instance=facil)
        if form.is_valid():
            form.instance.zone_fallback = get_object_or_404(Zone, pk=zone_id)
            form.save()
            return HttpResponseRedirect(reverse("zone_management", kwargs={"org_id": org_id, "zone_id": zone_id}))

    return {
        "org": org,
        "zone": zone,
        "facility": facil,
        "form": form,
    }


@require_authorized_admin
@render_to("control_panel/group_report.html")
def group_report(request, facility_id, group_id=None, org_id=None, zone_id=None):
    context = group_report_context(
        facility_id=facility_id,
        group_id=group_id or request.REQUEST.get("group", ""),
        topic_id=request.REQUEST.get("topic", ""),
        org_id=org_id,
        zone_id=zone_id
    )

    context["org"] = get_object_or_None(Organization, pk=org_id) if org_id else None
    context["zone"] = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    context["facility"] = get_object_or_404(Facility, pk=facility_id) if id != "new" else None
    context["group"] = get_object_or_None(FacilityGroup, pk=group_id)

    return context


@require_authorized_admin
@render_to("control_panel/group_users_management.html")
def facility_user_management(request, facility_id, group_id="", org_id=None, zone_id=None):
    group_id=group_id or request.REQUEST.get("group","")

    context = user_management_context(
        request=request,
        facility_id=facility_id,
        group_id=group_id,
        page=request.REQUEST.get("page","1"),
    )

    context["org"] = get_object_or_None(Organization, pk=org_id) if org_id else None
    context["zone"] = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    context["facility"] = get_object_or_404(Facility, pk=facility_id) if id != "new" else None
    context["group"] = get_object_or_None(FacilityGroup, pk=group_id)
    return context


@require_authorized_access_to_student_data
@render_to("control_panel/account_management.html")
def account_management(request, org_id=None):

    # Only log 'coachreport' activity for students, 
    #   (otherwise it's hard to compare teachers)
    if "facility_user" in request.session and not request.session["facility_user"].is_teacher and reverse("login") not in request.META.get("HTTP_REFERER", ""):
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.error("Failed to update student userlog activity: %s" % e)

    return student_view_context(request)


def get_users_from_group(group_id, facility=None):
    if group_id == "Ungrouped":
        return FacilityUser.objects \
            .filter(facility=facility, group__isnull=True) \
            .order_by("first_name", "last_name")
    elif not group_id:
        return []
    else:
        return get_object_or_404(FacilityGroup, pk=group_id).facilityuser_set.order_by("first_name", "last_name")


def user_management_context(request, facility_id, group_id, page=1, per_page=25):
    facility = Facility.objects.get(id=facility_id)
    groups = FacilityGroup.objects \
        .filter(facility=facility) \
        .order_by("name")

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
    }
    if users:
        context["pageurls"] = {"next_page": next_page_url, "prev_page": previous_page_url}
    return context
