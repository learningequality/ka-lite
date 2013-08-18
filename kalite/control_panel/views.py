import collections
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum, Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

import settings
from main import topicdata
from central.models import Organization
from control_panel.forms import ZoneForm, UploadFileForm
from main.models import ExerciseLog, VideoLog, UserLogSummary
from securesync.forms import FacilityForm
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device, Zone, SyncSession
from utils.decorators import require_authorized_admin


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
            "name": device.name or device.id,
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
def facility_usage(request, facility_id, org_id=None, zone_id=None):

    # Basic data
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facility = get_object_or_404(Facility, pk=facility_id)
    groups = FacilityGroup.objects.filter(facility=facility).order_by("name")
    users = FacilityUser.objects.filter(facility=facility).order_by("last_name")

    # Accumulating data
    len_all_exercises = len(topicdata.NODE_CACHE['Exercise'])

    group_data = collections.OrderedDict()
    user_data = collections.OrderedDict()
    for user in users:
        exercise_logs = ExerciseLog.objects.filter(user=user)
        exercise_stats = {"count": exercise_logs.count(), "total_mastery": exercise_logs.aggregate(Sum("complete"))["complete__sum"]}
        video_stats = {"count": VideoLog.objects.filter(user=user).count()}
        login_stats = UserLogSummary.objects.filter(user=user).aggregate(Sum("total_logins"), Sum("total_seconds"))

        user_data[user.pk] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.get_name(),
            "group": user.group,
            "total_logins": login_stats["total_logins__sum"] or 0,
            "total_hours": (login_stats["total_seconds__sum"] or 0)/3600.,
            "total_videos": video_stats["count"],
            "total_exercises": exercise_stats["count"],
            "pct_mastery": (exercise_stats["total_mastery"] or 0)/float(len_all_exercises),
        }

        group = user.group
        if group:
            if not group.pk in group_data:
                group_data[group.pk] = {
                    "name": group.name,
                    "total_logins": 0,
                    "total_hours": 0,
                    "total_users": 0,
                    "total_videos": 0,
                    "total_exercises": 0,
                    "pct_mastery": 0,
                }
            group_data[group.pk]["total_users"] += 1
            group_data[group.pk]["total_logins"] += user_data[user.pk]["total_logins"]
            group_data[group.pk]["total_hours"] += user_data[user.pk]["total_hours"]
            group_data[group.pk]["total_videos"] += user_data[user.pk]["total_videos"]
            group_data[group.pk]["total_exercises"] += user_data[user.pk]["total_exercises"]

            total_mastery_so_far = (group_data[group.pk]["pct_mastery"] * (group_data[group.pk]["total_users"] - 1) + user_data[user.pk]["pct_mastery"])
            group_data[group.pk]["pct_mastery"] =  total_mastery_so_far / group_data[group.pk]["total_users"]

    return {
        "org": org,
        "zone": zone,
        "facility": facility,
        "groups": group_data,
        "users": user_data,
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
