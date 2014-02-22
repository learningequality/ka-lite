from annoying.decorators import render_to
from collections import OrderedDict
from datetime import timedelta  # this is OK; central server code can be 2.7+

from django.db.models import Sum, Max, Count, F, Q, Min

from main.models import ExerciseLog, VideoLog
from securesync.models import SyncSession, Device
from shared.decorators import require_authorized_admin


@require_authorized_admin
@render_to("stats/admin_summary_page.html")
def recent_syncing(request, org_id=None, max_zones=20, chunk_size=100, ndays=None):
    ndays = ndays or int(request.GET.get("days", 7))

    ss = SyncSession.objects \
        .annotate( \
            ndevices=Count("client_device__devicezone__zone__id", distinct=True), \
        ) \
        .filter(models_uploaded__gt=0, timestamp__gt=F("timestamp") - timedelta(days=ndays)) \
        .order_by("-timestamp") \
        .values(
            "client_device__devicezone__zone__name", "client_device__devicezone__zone__id", "client_device__devicezone__zone__organization__id", \
            "ndevices", "timestamp", "models_uploaded", "client_device__name", "client_device__id", "client_version", "client_os", "client_device__devicemetadata__is_demo_device", \
        )

    # Apparently I can't group by zone.  So, will have to do manually
    zones = OrderedDict()
    cur_chunk = 0
    while len(zones) < max_zones and cur_chunk < ss.count():
        for session in ss[cur_chunk:cur_chunk+chunk_size]:
            if len(zones) >= max_zones:
                break
            zone_id = session["client_device__devicezone__zone__id"]
            if zone_id in zones:
                zones[zone_id]["nsessions"] += 1
                zones[zone_id]["nuploaded"] += session["models_uploaded"]
                zones[zone_id]["device"]["is_demo_device"] = zones[zone_id]["device"]["is_demo_device"] or session["client_device__devicemetadata__is_demo_device"]

            else:
                zones[zone_id] = {
                    "nsessions": 1,
                    "last_synced": session["timestamp"],
                    "nuploaded": session["models_uploaded"],
                    "name": session["client_device__devicezone__zone__name"],
                    "id": session["client_device__devicezone__zone__id"],
                    "organization": { "id": session["client_device__devicezone__zone__organization__id"] },
                    "device": {
                        "id": session["client_device__id"] or "ben",
                        "name": session["client_device__name"],
                        "os": session["client_os"],
                        "version": session["client_version"],
                        "is_demo_device": session["client_device__devicemetadata__is_demo_device"],
                    },
                }
        cur_chunk += chunk_size

    return {
        "days": ndays,
        "zones": zones,
    }


@require_authorized_admin
@render_to("stats/timelines.html")
def timelines(request):

    do = list(Device.objects \
        .exclude(devicemetadata__is_demo_device=True) \
        .annotate( \
            first_sess=Min("client_sessions__timestamp"),\
            nsess=Count("client_sessions", distinct=True), \
        ) \
        .order_by("first_sess") \
        .filter(nsess__gt=0) \
        .values("first_sess","nsess", "name", "devicezone__zone__name"))

    # Exercises completed (by date)
    eo = list(ExerciseLog.objects \
        .values("completion_timestamp", "signed_by__name", "signed_by__devicezone__zone__name") \
        .order_by("completion_timestamp") \
        .exclude(signed_by__devicemetadata__is_demo_device=True) \
        .filter(complete=True))

    # Videos completed (by date)
    vo = list(VideoLog.objects \
        .values("completion_timestamp", "signed_by__name", "signed_by__devicezone__zone__name") \
        .order_by("completion_timestamp") \
        .exclude(signed_by__devicemetadata__is_demo_device=True) \
        .filter(complete=True))

    return {
        "registrations": do,
        "exercises": eo,
        "videos": vo,
    }
