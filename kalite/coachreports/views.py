import json
import requests
import datetime
import re, settings
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string

from coachreports.forms import DataForm
from coachreports.api_views import get_data_form, stats_dict
from main import topicdata
from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser,FacilityGroup, DeviceZone, Device
from securesync.views import facility_required
from utils.decorators import require_login, require_admin
from utils.internet import StatusException
from utils.topic_tools import get_topic_exercises, get_topic_videos, get_all_midlevel_topics


def get_accessible_objects_from_request(request, facility):
    """Given a request, get all the facility/group/user objects relevant to the request,
    subject to the permissions of the user type.
    """
    
    # Options to select.  Note that this depends on the user.
    if request.user.is_superuser:
        groups = FacilityGroup.objects.filter(facility=facility)
        facilities = Facility.objects.all()
    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        if user.is_teacher:
            groups = FacilityGroup.objects.filter(facility=facility)
            facilities = Facility.objects.all()
        else:
            facilities = [user.facility]
            if user.group:
                groups = [request.session["facility_user"].group]
            else:
                groups = []
    else:
        facilities = [facility]
        groups = FacilityGroup.objects.filter(facility=facility)

    return (groups, facilities)


def plotting_metadata_context(request, facility, topic_path=[], *args, **kwargs):
    """Basic context for any plot: get the data form, a dictionary of stat definitions,
    and the full gamut of facility/group objects relevant to the request."""
    
    # Get the form, and retrieve the API data
    form = get_data_form(request, facility=facility, topic_path=topic_path, *args, **kwargs)

    (groups, facilities) = get_accessible_objects_from_request(request, facility)

    return {
        "form": form.data,
        "stats": stats_dict,
        "groups": groups,
        "facilities": facilities,
    }

####### view end-points ####

@require_admin
@facility_required
@render_to("coachreports/timeline_view.html")
def timeline_view(request, facility, xaxis="", yaxis=""):
    """timeline view (line plot, xaxis is time-related): just send metadata; data will be requested via AJAX"""
    return plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)


@require_admin
@facility_required
@render_to("coachreports/scatter_view.html")
def scatter_view(request, facility, xaxis="", yaxis=""):
    """Scatter view (scatter plot): just send metadata; data will be requested via AJAX"""
    return plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)


@require_login
@facility_required
@render_to("coachreports/student_view.html")
def student_view(request, facility, xaxis="pct_mastery", yaxis="ex:attempts"):
    """student view: data generated on the back-end.
    
    Student view lists a by-topic-summary of their activity logs.
    """
    
    user = get_object_or_None(FacilityUser, id=request.REQUEST.get("user_id"))
    user = user or request.session.get("facility_user",None)

    topics = get_all_midlevel_topics()
    topic_ids = [t['id'] for t in topics]
    topics = filter(partial(lambda n,ids: n['id'] in ids, ids=topic_ids), topicdata.NODE_CACHE['Topic'].values()) # real data, like paths

    any_data = False # whether the user has any data at all.
    exercise_logs = dict()
    video_logs = dict()
    exercise_sparklines = dict()
    stats = dict()
    topic_exercises = dict()
    for topic in topics:

        topic_exercises[topic['id']] = get_topic_exercises(path=topic['path'])
        n_exercises = len(topic_exercises[topic['id']])
        exercise_logs[topic['id']] = ExerciseLog.objects.filter(user=user, exercise_id__in=[t['name'] for t in topic_exercises[topic['id']]]).order_by("completion_timestamp")
        n_exercises_touched = len(exercise_logs[topic['id']])


        topic_videos = get_topic_videos(topic_id=topic['id'])
        n_videos = len(topic_videos)
        video_logs[topic['id']] = VideoLog.objects.filter(user=user, youtube_id__in=[tv['youtube_id'] for tv in topic_videos]).order_by("completion_timestamp")
        n_videos_touched = len(video_logs[topic['id']])

        exercise_sparklines[topic['id']] = [el.completion_timestamp for el in filter(lambda n: n.complete, exercise_logs[topic['id']])]

         # total streak currently a pct, but expressed in max 100; convert to proportion (like other percentages here)
        stats[topic['id']] = {
            "ex:pct_mastery":      0 if not n_exercises_touched else sum([el.complete for el in exercise_logs[topic['id']]])/float(n_exercises),
            "ex:pct_started":      0 if not n_exercises_touched else n_exercises_touched/float(n_exercises),
            "ex:average_points":   0 if not n_exercises_touched else sum([el.points for el in exercise_logs[topic['id']]])/float(n_exercises_touched),
            "ex:average_attempts": 0 if not n_exercises_touched else sum([el.attempts for el in exercise_logs[topic['id']]])/float(n_exercises_touched),
            "ex:average_streak":   0 if not n_exercises_touched else sum([el.streak_progress for el in exercise_logs[topic['id']]])/float(n_exercises_touched)/100.,
            "ex:total_struggling": 0 if not n_exercises_touched else sum([el.struggling for el in exercise_logs[topic['id']]]),
            "ex:last_completed":None if not n_exercises_touched else max([el.completion_timestamp or datetime.datetime(year=1900, month=1, day=1) for el in exercise_logs[topic['id']]]),

            "vid:pct_started":      0 if not n_videos_touched else n_videos_touched/float(n_videos),
            "vid:pct_completed":    0 if not n_videos_touched else sum([vl.complete for vl in video_logs[topic['id']]])/float(n_videos),
            "vid:total_minutes":      0 if not n_videos_touched else sum([vl.total_seconds_watched for vl in video_logs[topic['id']]])/60.,
            "vid:average_points":   0 if not n_videos_touched else sum([vl.points for vl in video_logs[topic['id']]])/float(n_videos_touched),
            "vid:last_completed":None if not n_videos_touched else max([vl.completion_timestamp or datetime.datetime(year=1900, month=1, day=1) for vl in video_logs[topic['id']]]),
        }
        any_data = any_data or n_exercises_touched>0 or n_videos_touched>0

    context = plotting_metadata_context(request, facility)
    return {
        "form": context["form"],
        "groups": context["groups"],
        "facilities": context["facilities"],
        "student": user,
        "topics": topics,
        "topic_ids": topic_ids,
        "exercises": topic_exercises,
        "exercise_logs": exercise_logs,
        "video_logs": video_logs,
        "exercise_sparklines": exercise_sparklines,
        "no_data": not any_data,
        "stats": stats,
        "stat_defs": [ # this order determines the order of display
            {"key": "ex:pct_mastery",          "title": "% Mastery",            "type": "pct"},
            {"key": "ex:pct_started",          "title": "% Started",  "type": "pct"},
            {"key": "ex:average_points",       "title": "Average Points",       "type": "float"},
            {"key": "ex:average_attempts",     "title": "Average Attempts",     "type": "float"},
            {"key": "ex:average_streak",       "title": "Average Streak",     "type": "pct"},
            {"key": "ex:total_struggling",     "title": "Struggling",     "type": "int"},
            {"key": "ex:last_completed",       "title": "Last Completed",       "type": "date"},
            {"key": "vid:pct_completed",       "title": "% Completed",  "type": "pct"},
            {"key": "vid:pct_started",         "title": "% Started",  "type": "pct"},
            {"key": "vid:total_minutes",        "title": "Average Minutes Watched","type": "float"},
            {"key": "vid:average_points",      "title": "Average Points",       "type": "float"},
            {"key": "vid:last_completed",      "title": "Last Completed",       "type": "date"},
        ]
    }


@require_admin
@facility_required
@render_to("coachreports/landing_page.html")
def landing_page(request, facility):
    """Landing page needs plotting context in order to generate the navbar"""
    return plotting_metadata_context(request, facility=facility)


@require_admin
@facility_required
@render_to("coachreports/tabular_view.html")
def tabular_view(request, facility, report_type="exercise"):
    """Tabular view also gets data server-side."""
    
    # Get a list of topics (sorted) and groups
    topics = get_all_midlevel_topics()
    (groups, facilities) = get_accessible_objects_from_request(request, facility)
    context = plotting_metadata_context(request, facility=facility)
    context.update({
        "report_types": ("exercise","video"),
        "request_report_type": report_type,
        "topics": topics,
    })

    # get querystring info
    topic_id = request.GET.get("topic", "")
    group_id = request.GET.get("group_id", "")
    
    # No valid data; just show generic
    if not group_id or not topic_id or not re.match("^[\w\-]+$", topic_id):
        return context

    group = get_object_or_404(FacilityGroup, pk=group_id)
    users = FacilityUser.objects.filter(group=group, is_teacher=False).order_by("last_name", "first_name")

    # We have enough data to render over a group of students
    # Get type-specific information
    if report_type=="exercise":
        # Fill in exercises
        exercises = get_topic_exercises(topic_id=topic_id)
        context["exercises"] = exercises

        # More code, but much faster
        exercise_names = [ex["name"] for ex in context["exercises"]]
        # Get students
        context["students"] = []
        for user in users:
            exlogs = ExerciseLog.objects.filter(user=user, exercise_id__in=exercise_names)
            log_ids = [log.exercise_id for log in exlogs]
            log_table = []
            for en in exercise_names:
                if en in log_ids:
                    log_table.append(exlogs[log_ids.index(en)])
                else:
                    log_table.append(None)

            context["students"].append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "id": user.id,
                "exercise_logs": log_table,
            })

    elif report_type=="video":
        # Fill in videos
        context["videos"] = get_topic_videos(topic_id=topic_id)

        # More code, but much faster
        video_ids = [vid["youtube_id"] for vid in context["videos"]]
        # Get students
        context["students"] = []
        for user in users:
            vidlogs = VideoLog.objects.filter(user=user, youtube_id__in=video_ids)
            log_ids = [log.youtube_id for log in vidlogs]
            log_table = []
            for yid in video_ids:
                if yid in log_ids:
                    log_table.append(vidlogs[log_ids.index(yid)])
                else:
                    log_table.append(None)

            context["students"].append({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "video_logs": log_table,
            })
    else:
        return HttpResponseNotFound(render_to_string("404_distributed.html", {}, context_instance=RequestContext(request)))

    return context
