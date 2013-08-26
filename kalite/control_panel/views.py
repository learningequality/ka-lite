import datetime
from annoying.decorators import render_to, wraps
from annoying.functions import get_object_or_None
from collections import OrderedDict, namedtuple

from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

import settings
from main import topicdata
from central.models import Organization
from control_panel.forms import ZoneForm, UploadFileForm
from main.models import ExerciseLog, VideoLog, UserLog, UserLogSummary
from securesync.forms import FacilityForm
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device, Zone, SyncSession
from shared.decorators import require_authorized_admin
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

    # Accumulate device data
    device_data = dict()
    for device in Device.objects.filter(devicezone__zone=zone):

        sync_sessions = SyncSession.objects.filter(client_device=device)
        user_activity = UserLogSummary.objects.filter(device=device)

        device_data[device.id] = {
            "name": device.name,
            "num_times_synced": sync_sessions.count(),
            "last_time_synced": sync_sessions.aggregate(Max("timestamp"))["timestamp__max"],
            "last_time_used":   None if user_activity.count() == 0 else user_activity.order_by("-end_datetime")[0],
            "counter": device.get_counter(),
        }

    # Accumulate facility data
    facility_data = dict()
    for facility in Facility.objects.by_zone(zone):

        user_activity = UserLogSummary.objects.filter(user__in=FacilityUser.objects.filter(facility=facility))

        facility_data[facility.id] = {
            "name": facility.name,
            "num_users":  FacilityUser.objects.filter(facility=facility).count(),
            "num_groups": FacilityGroup.objects.filter(facility=facility).count(),
            "id": facility.id,
            "last_time_used":   None if user_activity.count() == 0 else user_activity.order_by("-end_datetime")[0],
        }

    return {
        "org": org,
        "zone": zone,
        "facilities": facility_data,
        "devices": device_data,
        "upload_form": UploadFileForm()
    }



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
@render_to_csv(["students"], key_label="user_id")
def facility_usage(request, facility_id, org_id=None, zone_id=None, frequency=None):

    # Basic data
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facility = get_object_or_404(Facility, pk=facility_id)
    groups = FacilityGroup.objects.filter(facility=facility).order_by("name")
    students = FacilityUser.objects.filter(facility=facility, is_teacher=False).order_by("last_name", "first_name", "username")

    # compute period start and end
    frequency = frequency or request.GET.get("fequency")
    if frequency == "months":  # only works for months ATM
        cur_date = datetime.datetime.now()
        first_this_month = datetime.datetime(year=cur_date.year, month=cur_date.month - 1, day=cur_date.day, hour=23, minute=59, second=59)
        period_end = first_this_month - datetime.timedelta(days=1)
        period_start = datetime.datetime(year=period_end.year, month=period_end.month, day=1)

    # Now compute stats, based on queried data
    len_all_exercises = len(topicdata.NODE_CACHE['Exercise'])
    student_data = OrderedDict()
    group_data = OrderedDict()
    for student in students:
        exercise_logs = ExerciseLog.objects.filter(user=student)
        video_logs = VideoLog.objects.filter(user=student)
        login_logs = UserLogSummary.objects.filter(user=student)

        # filter results
        if frequency:
            exercise_logs = exercise_logs.filter(completion_timestamp__gte=period_start, completion_timestamp__lte=period_end)
            video_logs = video_logs.filter(completion_timestamp__gte=period_start, completion_timestamp__lte=period_end)
            login_logs = login_logs.filter(start_datetime__gte=period_start, end_datetime__lte=period_end)

        exercise_stats = {
            "count": exercise_logs.count(),
            "total_mastery": exercise_logs.aggregate(Sum("complete"))["complete__sum"],
            "mastered_exercises": [elog.exercise_id for elog in exercise_logs if elog.complete],
        }
        video_stats = {"count": VideoLog.objects.filter(user=student).count()}
        login_stats = UserLogSummary.objects \
            .filter(user=student, activity_type=UserLog.get_activity_int("login")) \
            .aggregate(Sum("count"), Sum("total_seconds"))

        # Had to add one-by-one, to get OrderedDict to work.
        #   OrderedDict controls the order of the columns
        student_data[student.pk] = OrderedDict()
        student_data[student.pk]["first_name"] = student.first_name
        student_data[student.pk]["last_name"] = student.last_name
        student_data[student.pk]["username"] = student.username
        student_data[student.pk]["group"] = student.group
        student_data[student.pk]["total_logins"] = login_stats["count__sum"] or 0
        student_data[student.pk]["total_hours"] = (login_stats["total_seconds__sum"] or 0)/3600.
        student_data[student.pk]["total_videos"] = video_stats["count"]
        student_data[student.pk]["total_exercises"] = exercise_stats["count"]
        student_data[student.pk]["pct_mastery"] = (exercise_stats["total_mastery"] or 0)/float(len_all_exercises)
        student_data[student.pk]["exercises_mastered"] = exercise_stats["mastered_exercises"]

        # Add group data.  Allow a fake group "Ungrouped"
        group_pk = getattr(student.group, "pk", None)
        group_name = getattr(student.group, "name", "Ungrouped")
        if not group_pk in group_data:
            group_data[group_pk] = {
                "name": group_name,
                "total_logins": 0,
                "total_hours": 0,
                "total_students": 0,
                "total_videos": 0,
                "total_exercises": 0,
                "pct_mastery": 0,
            }
        group_data[group_pk]["total_students"] += 1
        group_data[group_pk]["total_logins"] += student_data[student.pk]["total_logins"]
        group_data[group_pk]["total_hours"] += student_data[student.pk]["total_hours"]
        group_data[group_pk]["total_videos"] += student_data[student.pk]["total_videos"]
        group_data[group_pk]["total_exercises"] += student_data[student.pk]["total_exercises"]

        total_mastery_so_far = (group_data[group_pk]["pct_mastery"] * (group_data[group_pk]["total_students"] - 1) + student_data[student.pk]["pct_mastery"])
        group_data[group_pk]["pct_mastery"] =  total_mastery_so_far / group_data[group_pk]["total_students"]

    return {
        "org": org,
        "zone": zone,
        "facility": facility,
        "groups": group_data,
        "students": student_data,
        "date_range": [period_start, period_end] if frequency else [None, None],
    }


@require_authorized_admin
@render_to("control_panel/device_management.html")
def device_management(request, device_id, org_id=None, zone_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    device = get_object_or_404(Device, pk=device_id)

    sync_sessions = SyncSession.objects.filter(client_device=device)
    return {
        "org": org,
        "zone": zone,
        "device": device,
        "sync_sessions": sync_sessions,
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


def get_users_from_group(group_id, facility=None):
    if group_id == "Ungrouped":
        return FacilityUser.objects.filter(facility=facility,group__isnull=True)
    elif not group_id:
        return []
    else:
        return get_object_or_404(FacilityGroup, pk=group_id).facilityuser_set.order_by("first_name", "last_name")


def user_management_context(request, facility_id, group_id, page=1, per_page=25):
    facility = Facility.objects.get(id=facility_id)
    groups = FacilityGroup.objects.filter(facility=facility)

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
    }
    if users:
        context["pageurls"] = {"next_page": next_page_url, "prev_page": previous_page_url}
    return context
