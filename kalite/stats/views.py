import datetime
import os
from annoying.decorators import render_to
from collections import Counter, OrderedDict
from datetime import timedelta  # this is OK; central server code can be 2.7+

from django.db.models import Sum, Max, Count, F, Q, Min

from . import stats_logger
from i18n import get_video_language, get_video_id
from main.models import ExerciseLog, VideoLog
from main.topic_tools import get_id2slug_map
from securesync.models import SyncSession, Device
from settings import LOG as logging
from shared.decorators import require_authorized_admin


@require_authorized_admin
@render_to("stats/syncing.html")
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
def timelines(request, ndays=None):
    ndays = ndays or int(request.GET.get("days", 1))

    registrations = list(Device.objects \
        .exclude(devicemetadata__is_demo_device=True) \
        .annotate( \
            first_sess=Min("client_sessions__timestamp"),\
            nsess=Count("client_sessions", distinct=True), \
        ) \
        .values("first_sess", "nsess", "name", "devicezone__zone__name") \
        .order_by("first_sess") \
        .filter(nsess__gt=0, first_sess__gt=F("first_sess") - timedelta(days=ndays)))

    # Exercises completed (by date)
    exercises = list(ExerciseLog.objects \
        .values("completion_timestamp", "signed_by__name", "signed_by__devicezone__zone__name") \
        .order_by("completion_timestamp") \
        .exclude(signed_by__devicemetadata__is_demo_device=True) \
        .filter(complete=True, completion_timestamp__gt=F("completion_timestamp") - timedelta(days=ndays)))

    # Videos completed (by date)
    videos = list(VideoLog.objects \
        .values("completion_timestamp", "signed_by__name", "signed_by__devicezone__zone__name") \
        .order_by("completion_timestamp") \
        .exclude(signed_by__devicemetadata__is_demo_device=True) \
        .filter(complete=True, completion_timestamp__gt=F("completion_timestamp") - timedelta(days=ndays)))

    return {
        "registrations": registrations,
        "exercises": exercises,
        "videos": videos,
    }



def sorted_dict(d, key=lambda t: t[1], reverse=True, **kwargs):
    return OrderedDict(sorted(d.items(), key=key, reverse=reverse, **kwargs))

def sum_counter(d_in, fn, **kwargs):
    d_out = dict()
    for key, val in d_in.iteritems():
        new_key = fn(key)
        d_out[new_key] = val + d_out.get(new_key, 0)
    return sorted_dict(d_out, **kwargs)


@require_authorized_admin
@render_to("stats/logs.html")
def show_logs(request, ndays=None):
    """Show file-based logging info for video downloads, language packs, and subtitles"""
    ndays = ndays or int(request.GET.get("days", 7))

    def get_logger_filename(logger_type):
        return stats_logger(logger_type).handlers[0].baseFilename

    def parse_data(logger_type, data_fields, windowsize=128, ndays=None):
        parsed_data = {}
        nparts = len(data_fields)
        summary_data = dict([(fld, {}) for fld in (data_fields + ["date"])])

        filepath = get_logger_filename(logger_type)
        if not os.path.exists(filepath):
            return (parsed_data, summary_data)

        # Group by ip, date, and youtube_id
        old_data = ""
        first_loop = True
        last_loop = False
        with open(filepath, "r") as fp:
            fp.seek(0, 2)  # go to the end of the stream
            while True:
                # Read the next chunk of data
                try:
                    # Get the data
                    try:
                        if first_loop:
                            fp.seek(-windowsize, 1)  # go backwards by a few
                            first_loop = False
                        else:
                            fp.seek(-2 * windowsize, 1)  # go backwards by a few

                        cur_data = fp.read(windowsize) + old_data
                    except:
                        if last_loop and not old_data:
                            raise
                        elif last_loop:
                            cur_data = old_data
                            old_data = ""
                        else:
                            last_loop = True
                            fp.seek(0)
                            cur_data = fp.read(windowsize) + old_data  # could be some overlap...

                    if not cur_data:
                        break;
                except:
                    break

                # Parse the data
                lines = cur_data.split("\n")
                old_data = lines[0] if len(lines) > 1 else ""
                new_data = lines[1:] if len(lines) > 1 else lines
                for l in new_data:
                    if not l:
                        continue

                    # All start with a date
                    parts = l.split(" - ", 2)
                    if len(parts) != 2:
                        continue
                    tim = parts[0]
                    dat = tim.split(" ")[0]

                    # Validate that this date is within the accepted range
                    parsed_date = datetime.datetime.strptime(dat, "%Y-%m-%d")
                    logging.debug("%s %s" % (parsed_date, (datetime.datetime.now() - timedelta(days=ndays))))
                    if ndays is not None and datetime.datetime.now() - timedelta(days=ndays) > parsed_date:
                        last_loop = True
                        old_data = ""
                        break;

                    # The rest is semicolon-delimited
                    parts = parts[1].split(";")  # vd;127.0.0.1;xvnpSRO9IDM

                    # Now save things off
                    parsed_data[tim] = dict([(data_fields[idx], parts[idx]) for idx in range(nparts)])
                    summary_data["date"][dat] = 1 + summary_data["date"].get(dat, 0)
                    for idx in range(nparts):
                        summary_data[data_fields[idx]][parts[idx]] = 1 + summary_data[data_fields[idx]].get(parts[idx], 0)

        for key, val in summary_data.iteritems():
            summary_data[key] = sorted_dict(val, key=lambda t: t[0])

        return (parsed_data, summary_data)

    (video_raw_data, video_summary_data) = parse_data("videos", ["task_id", "ip_address", "youtube_id"], ndays=ndays)
    (lp_raw_data, lp_summary_data)       = parse_data("language_packs", ["task_id", "ip_address", "lang_code", "version"], ndays=ndays)
    (srt_raw_data, srt_summary_data)     = parse_data("subtitles", ["task_id", "ip_address", "lang_code", "youtube_id"], ndays=ndays)

    return {
        "ndays": ndays,
        "videos": {
            "raw": video_raw_data,
            "dates": video_summary_data["date"],
            "ips": video_summary_data["ip_address"],
            "slugs": sum_counter(video_summary_data["youtube_id"], fn=lambda yid: get_id2slug_map().get(get_video_id(yid))),
            "lang_codes": sum_counter(video_summary_data["youtube_id"], fn=lambda yid: get_video_language(yid)),
        },
        "language_packs": {
            "raw": lp_raw_data,
            "dates": lp_summary_data["date"],
            "ips": lp_summary_data["ip_address"],
            "lang_codes": lp_summary_data["lang_code"],
            "versions": lp_summary_data["version"],
        },
        "subtitles": {
            "raw": srt_raw_data,
            "dates": srt_summary_data["date"],
            "ips": srt_summary_data["ip_address"],
            "lang_codes": srt_summary_data["lang_code"],
        },
    }
