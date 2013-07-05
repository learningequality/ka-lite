import collections
import datetime
import json
import pickle
import re
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from decorator.decorator import decorator

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

import kalite
import settings
from main import topicdata
from central.models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile, FeedListing, Subscription
from control_panel.forms import ZoneForm, UploadFileForm
from main.models import ExerciseLog, VideoLog, UserLogSummary
from securesync.api_client import SyncClient
from securesync.forms import FacilityForm
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device
from securesync.models import Zone, SyncSession
from securesync.model_sync import save_serialized_models, get_serialized_models
from utils.decorators import authorized_login_required


@authorized_login_required
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



@authorized_login_required
def zone_data_upload(request, zone_id, org_id=None):
    if request.method != 'POST':
        return HttpResponseForbidden()

    # Validate form and get file data
    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseServerError("Unparseable POST request")
    data = pickle.loads(request.FILES['file'].read())

    # TODO(bcipolli): why should I trust the signer.  Who are you to me?
    signed_by = serializers.deserialize("json", data["signed_by"]).next().object
    if signed_by == Device.get_own_device():
        settings.LOG.debug("upload: I trust myself.")
    elif signed_by.get_zone.id == zone_id:
        settings.LOG.debug("upload: I trust others that are on this zone.")
    else:
        return HttpResponseForbidden("upload: You're not on this zone, you can't use zone upload.  Use your own zone, or do this from org upload.")

    # Verify the signatures on the data
    if not signed_by.get_key().verify(data["devices"],  data["devices_signature"]):
        return HttpResponseForbidden("Devices are corrupted")
    if not signed_by.get_key().verify(data["models"],  data["models_signature"]):
        return HttpResponseForbidden("Models are corrupted")

    # Save the data and check for errors
    result = save_serialized_models(data["devices"], increment_counters=False, client_version=signed_by.version) #version is a lie
    if result.get("errors", 0):
        return HttpResponseServerError("Errors uploading devices: %s" % str(result["errors"]))
    result = save_serialized_models(data["models"], increment_counters=False, client_version=signed_by.version) #version is a lie
    if result.get("errors", 0):
        return HttpResponseServerError("Errors uploading models: %s" % str(result["errors"]))

    # Reload the page
    return HttpResponseRedirect(reverse("zone_management", kwargs={"org_id": org_id, "zone_id": zone_id}))


@authorized_login_required
def zone_data_download(request, zone_id, org_id=None):
    zone = Zone.objects.get(id=zone_id)
    own_device = Device.get_own_device()
    device_counters = dict()
    for dz in DeviceZone.objects.filter(zone=zone):
        device = dz.device
        device_counters[device.id] = 0

    # Get the data
    sync_client = SyncClient()
    sync_client.start_session()
    data = {
        "devices": sync_client.download_devices(server_counters = device_counters, save=False)[1],
        "models": sync_client.download_models(device_counters, save=False)[1]['models']
    }
    #sync_client.end_session()

    # Sign the data
    data["devices_signature"] = own_device.get_key().sign(data["devices"])
    data["models_signature"] = own_device.get_key().sign(data["models"])
    data["signed_by"] = serializers.serialize("json", [own_device], ensure_ascii=True)

    # Stream the data back to the user
    user_facing_filename = "data-zone-%s-date-%s-v%s.pkl" % (zone.name, str(datetime.datetime.now()), kalite.VERSION)
    user_facing_filename = user_facing_filename.replace(" ","_").replace("%","_")
    response = HttpResponse(content=pickle.dumps(data), mimetype='text/pickle', content_type='text/pickle')
    response['Content-Disposition'] = 'attachment; filename="%s"' % user_facing_filename

    return response



@authorized_login_required
@render_to("control_panel/zone_management.html")
def zone_management(request, zone_id, org_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_404(Zone, pk=zone_id)# if zone_id != "new" else None

    # Accumulate device data
    device_zones = DeviceZone.objects.filter(zone=zone)
    device_data = dict()
    for device_zone in device_zones:
        device = device_zone.device
        num_times_synced = SyncSession.objects.filter(client_device=device).count()
        device_data[device.id] = {
            "name": device.name,
            "num_times_synced": num_times_synced,
            "last_time_synced": None if num_times_synced == 0 else SyncSession.objects.filter(client_device=device, ).order_by("-timestamp")[0].timestamp,
        }

    # Accumulate facility data
    facility_data = dict()
    for facility in Facility.from_zone(zone):
        facility_data[facility.id] = {
            "name": facility.name,
            "num_users":  FacilityUser.objects.filter(facility=facility).count(),
            "num_groups": FacilityGroup.objects.filter(facility=facility).count(),
            "id": facility.id,
        }

    return {
        "org": org,
        "zone": zone,
        "facilities": facility_data,
        "devices": device_data,
        "upload_form": UploadFileForm()
    }



#TODO(bcipolli) I think this will be deleted on the central server side
@authorized_login_required
@render_to("control_panel/facility_management.html")
def facility_management(request, zone_id, org_id=None):
    facilities = Facility.objects.by_zone(zone_id)
    return {
        "zone_id": zone_id,
        "facilities": facilities,
    }

@authorized_login_required
@render_to("control_panel/facility_usage.html")
def facility_usage(request, facility_id, org_id=None, zone_id=None):

    # Basic data
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facility = get_object_or_404(Facility, pk=facility_id)
    groups = FacilityGroup.objects.filter(facility=facility).order_by("name")
    users = FacilityUser.objects.filter(facility=facility).order_by("last_name")

    # Accumulating data
    group_data = collections.OrderedDict()
    user_data = collections.OrderedDict()
    for user in users:
        exercise_stats = {"count": ExerciseLog.objects.filter(user=user).count()}
        video_stats = {"count": VideoLog.objects.filter(user=user).count()}
        login_stats = UserLogSummary.objects.filter(user=user).aggregate(Sum("total_logins"), Sum("total_seconds"))

        user_data[user.pk] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.get_name,
            "group_name": getattr(user.group, "name", None),
            "total_logins": login_stats["total_logins__sum"] or 0,
            "total_hours": login_stats["total_seconds__sum"]/3600. if login_stats["total_seconds__sum"] else 0.,
            "total_videos": video_stats["count"],
            "total_exercises": exercise_stats["count"],
            "total_mastery": "NYI",
        }

        group = user.group
        if group:
            if not group.pk in group_data:
                group_data[group.pk] = {
                    "name": group.name,
                    "total_logins": "NYI",
                    "total_hours": "NYI",
                    "total_users": 0,
                    "total_videos": 0,
                    "total_exercises": 0,
                    "total_mastery": "NYI",
                }
            group_data[group.pk]["total_users"] += 1
            group_data[group.pk]["total_videos"] += user_data[user.pk]["total_videos"]
            group_data[group.pk]["total_exercises"] += user_data[user.pk]["total_exercises"]

    return {
        "org": org,
        "zone": zone,
        "facility": facility,
        "groups": group_data,
        "users": user_data,
    }


@authorized_login_required
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


@authorized_login_required
@render_to("control_panel/facility_form.html")
def facility_form(request, facility_id, org_id=None, zone_id=None):
    org = get_object_or_None(Organization, pk=org_id) if org_id else None
    zone = get_object_or_None(Zone, pk=zone_id) if zone_id else None
    facil = get_object_or_404(Facility, pk=facility_id) if id != "new" else None

    if request.method == "POST":
        form = FacilityForm(data=request.POST, instance=facil)
        if form.is_valid():
            form.instance.zone_fallback = get_object_or_404(Zone, pk=zone_id)
            form.save()
            if not facil:
                facil = None
            return HttpResponseRedirect(reverse("zone_management", kwargs={"org_id": org_id, "zone_id": zone_id}))
    else:
        form = FacilityForm(instance=facil)
    return {
        "org": org,
        "zone": zone,
        "facility": facil,
        "form": form,
    }

@authorized_login_required
@render_to("control_panel/coach_reports.html")
def facility_mastery(request, org_id, zone_id, facility_id):
    raise NotImplementedError()


@authorized_login_required
def facility_data_download(request, org_id, zone_id, facility_id):
    raise NotImplementedError()


@authorized_login_required
def facility_data_upload(request, org_id, zone_id, facility_id):
    raise NotImplementedError()


@authorized_login_required
@render_to("control_panel/group_report.html")
def group_report(request, facility_id, group_id, org_id=None, zone_id=None):
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

@authorized_login_required
@render_to("control_panel/facility_user_management.html")
def facility_user_management(request, facility_id, group_id="", org_id=None, zone_id=None):
    group_id=group_id or request.REQUEST.get("group","")

    context = facility_users_context(
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



def group_report_context(facility_id, group_id, topic_id, org_id=None, zone_id=None):
    facility = get_object_or_404(Facility, pk=facility_id)

    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    groups = FacilityGroup.objects.filter(facility=facility)
    paths = dict((key, val["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "facility": facility,
        "groups": groups,
        "group_id": group_id,
        "topics": topics,
        "topic_id": topic_id,
        "exercise_paths": json.dumps(paths),
    }

    if context["group_id"] and context["topic_id"] and re.match("^[\w\-]+$", context["topic_id"]):
        exercises = json.loads(open("%stopicdata/%s.json" % (settings.DATA_PATH, context["topic_id"])).read())
        exercises = sorted(exercises, key=lambda e: (e["h_position"], e["v_position"]))
        context["exercises"] = [{
            "display_name": ex["display_name"],
            "description": ex["description"],
            "short_display_name": ex["short_display_name"],
            "path": topicdata.NODE_CACHE["Exercise"][ex["name"]]["path"],
        } for ex in exercises]


        context["students"] = [{
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "exercise_logs": [get_object_or_None(ExerciseLog, user=user, exercise_id=ex["name"]) for ex in exercises],
        } for user in get_users_from_group(context['group_id'], facility=facility)]

    return context


def facility_users_context(request, facility_id, group_id, page=1, per_page=25):
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


#@post_only
@authorized_login_required
def device_data_upload(request, org_id, zone_id, device_id):
    if request.method != 'POST':
        return HttpResponseForbidden()

    form = UploadFileForm(request.POST, request.FILES)
    if not form.is_valid():
        return HttpResponseServerError("Unparseable POST request")

    models_json = request.FILES['file'].read()
    save_serialized_models(models_json, increment_counters=True, client_version=kalite.VERSION) #version is a lie


    return HttpResponseRedirect(reverse("zone_management", kwargs={"org_id": org_id, "zone_id": zone_id}))


@authorized_login_required
def device_data_download(request, org_id, zone_id, device_id):
    device = get_object_or_404(Device, pk=device_id)
    zone = get_object_or_None(Zone, pk=zone_id)

    device_counters = { device.id: 0 } # get everything

    # Get the data
    serialized_models = get_serialized_models(device_counters=device_counters, limit=100000000, zone=zone, include_count=True, client_version=kalite.VERSION)

    # Stream the data back to the user."
    user_facing_filename = "data-device-%s-date-%s-v%s.json" % (device.name, str(datetime.datetime.now()), kalite.VERSION)
    user_facing_filename = user_facing_filename.replace(" ","_").replace("%","_")
    response = HttpResponse(content=serialized_models['models'], mimetype='text/json', content_type='text/json')
    response['Content-Disposition'] = 'attachment; filename="%s"' % user_facing_filename
    return response
