import json
import requests
import datetime
import re
import settings
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from .api_views import get_data_form, stats_dict
from main.topicdata import ID2SLUG_MAP, NODE_CACHE
from main.models import VideoLog, ExerciseLog, VideoFile, UserLog
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device
from securesync.views import facility_required
from settings import LOG as logging
from shared.decorators import require_authorized_access_to_student_data, require_authorized_admin, get_user_from_request
from utils.general import max_none
from utils.internet import StatusException
from utils.topic_tools import get_topic_exercises, get_topic_videos, get_knowledgemap_topics


def get_accessible_objects_from_logged_in_user(request):
    """Given a request, get all the facility/group/user objects relevant to the request,
    subject to the permissions of the user type.
    """

    # Options to select.  Note that this depends on the user.
    if request.user.is_superuser:
        facilities = Facility.objects.all()
        # Groups is now a list of objects with a key for facility id, and a key
        # for the list of groups at that facility.
        # TODO: Make this more efficient.
        groups = [{"facility": facilitie.id, "groups": FacilityGroup.objects.filter(facility=facilitie)} for facilitie in facilities]
    elif "facility_user" in request.session:
        user = request.session["facility_user"]
        if user.is_teacher:
            facilities = Facility.objects.all()
            groups = [{"facility": facilitie.id, "groups": FacilityGroup.objects.filter(facility=facilitie)} for facilitie in facilities]
        else:
            # Students can only access their group
            facilities = [user.facility]
            if not user.group:
                groups = []
            else:
                groups = [{"facility": user.facility.id, "groups": FacilityGroup.objects.filter(id=request.session["facility_user"].group)}]
    else:
        facilities = [facility]
        groups = [{"facility": facility.id, "groups": FacilityGroup.objects.filter(facility=facility)}]

    return (groups, facilities)


def plotting_metadata_context(request, facility=None, topic_path=[], *args, **kwargs):
    """Basic context for any plot: get the data form, a dictionary of stat definitions,
    and the full gamut of facility/group objects relevant to the request."""

    # Get the form, and retrieve the API data
    form = get_data_form(request, facility=facility, topic_path=topic_path, *args, **kwargs)

    (groups, facilities) = get_accessible_objects_from_logged_in_user(request)

    return {
        "form": form.data,
        "stats": stats_dict,
        "groups": groups,
        "facilities": facilities,
    }

# view end-points ####


@require_authorized_admin
@facility_required
@render_to("coachreports/timeline_view.html")
def timeline_view(request, facility, xaxis="", yaxis=""):
    """timeline view (line plot, xaxis is time-related): just send metadata; data will be requested via AJAX"""
    return plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)


@require_authorized_admin
@facility_required
@render_to("coachreports/scatter_view.html")
def scatter_view(request, facility, xaxis="", yaxis=""):
    """Scatter view (scatter plot): just send metadata; data will be requested via AJAX"""
    return plotting_metadata_context(request, facility=facility, xaxis=xaxis, yaxis=yaxis)


@require_authorized_access_to_student_data
@render_to("coachreports/student_view.html")
def student_view(request, xaxis="pct_mastery", yaxis="ex:attempts"):
    """
    Student view: data generated on the back-end.

    Student view lists a by-topic-summary of their activity logs.
    """
    return student_view_context(request=request, xaxis=xaxis, yaxis=yaxis)


@require_authorized_access_to_student_data
def student_view_context(request, xaxis="pct_mastery", yaxis="ex:attempts"):
    """
    Context done separately, to be importable for similar pages.
    """
    user = get_user_from_request(request=request)
    topic_slugs = [t["id"] for t in get_knowledgemap_topics()]
    topics = [NODE_CACHE["Topic"][slug] for slug in topic_slugs]

    user_id = user.id
    exercise_logs = list(ExerciseLog.objects \
        .filter(user=user) \
        .values("exercise_id", "complete", "points", "attempts", "streak_progress", "struggling", "completion_timestamp"))
    video_logs = list(VideoLog.objects \
        .filter(user=user) \
        .values("youtube_id", "complete", "total_seconds_watched", "points", "completion_timestamp"))

    exercise_sparklines = dict()
    stats = dict()
    topic_exercises = dict()
    topic_videos = dict()
    exercises_by_topic = dict()
    videos_by_topic = dict()

    # Categorize every exercise log into a "midlevel" exercise
    for elog in exercise_logs:
        topic = set(NODE_CACHE["Exercise"][elog["exercise_id"]]["parents"]).intersection(set(topic_slugs))
        topic = topic.pop()
        if not topic in topic_exercises:
            topic_exercises[topic] = get_topic_exercises(path=NODE_CACHE["Topic"][topic]["path"])
        exercises_by_topic[topic] = exercises_by_topic.get(topic, []) + [elog]

    # Categorize every video log into a "midlevel" exercise.
    for vlog in video_logs:
        topic = set(NODE_CACHE["Video"][ID2SLUG_MAP[vlog["youtube_id"]]]["parents"]).intersection(set(topic_slugs)).pop()
        if not topic in topic_videos:
            topic_videos[topic] = get_topic_videos(path=NODE_CACHE["Topic"][topic]["path"])
        videos_by_topic[topic] = videos_by_topic.get(topic, []) + [vlog]


    # Now compute stats
    for topic in topic_slugs:#set(topic_exercises.keys()).union(set(topic_videos.keys())):
        n_exercises = len(topic_exercises.get(topic, []))
        n_videos = len(topic_videos.get(topic, []))

        exercises = exercises_by_topic.get(topic, [])
        videos = videos_by_topic.get(topic, [])
        n_exercises_touched = len(exercises)
        n_videos_touched = len(videos)

        exercise_sparklines[topic] = [el["completion_timestamp"] for el in filter(lambda n: n["complete"], exercises)]

         # total streak currently a pct, but expressed in max 100; convert to
         # proportion (like other percentages here)
        stats[topic] = {
            "ex:pct_mastery":      0 if not n_exercises_touched else sum([el["complete"] for el in exercises]) / float(n_exercises),
            "ex:pct_started":      0 if not n_exercises_touched else n_exercises_touched / float(n_exercises),
            "ex:average_points":   0 if not n_exercises_touched else sum([el["points"] for el in exercises]) / float(n_exercises_touched),
            "ex:average_attempts": 0 if not n_exercises_touched else sum([el["attempts"] for el in exercises]) / float(n_exercises_touched),
            "ex:average_streak":   0 if not n_exercises_touched else sum([el["streak_progress"] for el in exercises]) / float(n_exercises_touched) / 100.,
            "ex:total_struggling": 0 if not n_exercises_touched else sum([el["struggling"] for el in exercises]),
            "ex:last_completed": None if not n_exercises_touched else max_none([el["completion_timestamp"] or None for el in exercises]),

            "vid:pct_started":      0 if not n_videos_touched else n_videos_touched / float(n_videos),
            "vid:pct_completed":    0 if not n_videos_touched else sum([vl["complete"] for vl in videos]) / float(n_videos),
            "vid:total_minutes":      0 if not n_videos_touched else sum([vl["total_seconds_watched"] for vl in videos]) / 60.,
            "vid:average_points":   0. if not n_videos_touched else float(sum([vl["points"] for vl in videos]) / float(n_videos_touched)),
            "vid:last_completed": None if not n_videos_touched else max_none([vl["completion_timestamp"] or None for vl in videos]),
        }

    context = plotting_metadata_context(request)

    return {
        "form": context["form"],
        "groups": context["groups"],
        "facilities": context["facilities"],
        "student": user,
        "topics": topics,
        "exercises": topic_exercises,
        "exercise_logs": exercises_by_topic,
        "video_logs": videos_by_topic,
        "exercise_sparklines": exercise_sparklines,
        "no_data": not exercise_logs and not video_logs,
        "stats": stats,
        "stat_defs": [  # this order determines the order of display
            {"key": "ex:pct_mastery",      "title": _("% Mastery"),        "type": "pct"},
            {"key": "ex:pct_started",      "title": _("% Started"),        "type": "pct"},
            {"key": "ex:average_points",   "title": _("Average Points"),   "type": "float"},
            {"key": "ex:average_attempts", "title": _("Average Attempts"), "type": "float"},
            {"key": "ex:average_streak",   "title": _("Average Streak"),   "type": "pct"},
            {"key": "ex:total_struggling", "title": _("Struggling"),       "type": "int"},
            {"key": "ex:last_completed",   "title": _("Last Completed"),   "type": "date"},
            {"key": "vid:pct_completed",   "title": _("% Completed"),      "type": "pct"},
            {"key": "vid:pct_started",     "title": _("% Started"),        "type": "pct"},
            {"key": "vid:total_minutes",   "title": _("Average Minutes Watched"),"type": "float"},
            {"key": "vid:average_points",  "title": _("Average Points"),   "type": "float"},
            {"key": "vid:last_completed",  "title": _("Last Completed"),   "type": "date"},
        ]
    }


@require_authorized_admin
@facility_required
@render_to("coachreports/landing_page.html")
def landing_page(request, facility):
    """Landing page needs plotting context in order to generate the navbar"""
    return plotting_metadata_context(request, facility=facility)


@require_authorized_admin
@facility_required
@render_to("coachreports/tabular_view.html")
def tabular_view(request, facility, report_type="exercise"):
    """Tabular view also gets data server-side."""

    # Get a list of topics (sorted) and groups
    topics = get_knowledgemap_topics()
    (groups, facilities) = get_accessible_objects_from_logged_in_user(request)
    context = plotting_metadata_context(request, facility=facility)
    context.update({
        "report_types": ("exercise", "video"),
        "request_report_type": report_type,
        "topics": topics,
    })

    # get querystring info
    topic_id = request.GET.get("topic", "")
    # No valid data; just show generic
    if not topic_id or not re.match("^[\w\-]+$", topic_id):
        return context

    group_id = request.GET.get("group", "")
    if group_id:
        # Narrow by group
        users = FacilityUser.objects.filter(
            group=group_id, is_teacher=False).order_by("last_name", "first_name")

    elif facility:
        # Narrow by facility
        search_groups = [dict["groups"] for dict in groups if dict["facility"] == facility.id]
        assert len(search_groups) <= 1, "should only have one or zero matches."

        # Return groups and ungrouped
        search_groups = search_groups[0]  # make sure to include ungrouped students
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None, facility=facility), is_teacher=False).order_by("last_name", "first_name")

    else:
        # Show all (including ungrouped)
        for groups_dict in groups:
            search_groups += groups_dict["groups"]
        users = FacilityUser.objects.filter(
            Q(group__in=search_groups) | Q(group=None), is_teacher=False).order_by("last_name", "first_name")

    # We have enough data to render over a group of students
    # Get type-specific information
    if report_type == "exercise":
        # Fill in exercises
        exercises = get_topic_exercises(topic_id=topic_id)
        exercises = sorted(exercises, key=lambda e: (e["h_position"], e["v_position"]))
        context["exercises"] = exercises

        # More code, but much faster
        exercise_names = [ex["name"] for ex in context["exercises"]]
        # Get students
        context["students"] = []
        exlogs = ExerciseLog.objects \
            .filter(user__in=users, exercise_id__in=exercise_names) \
            .order_by("user__last_name", "user__first_name")\
            .values("user__id", "struggling", "complete", "exercise_id")
        exlogs = list(exlogs)  # force the query to be evaluated

        exlog_idx = 0
        for user in users:
            log_table = {}
            while exlog_idx < len(exlogs) and exlogs[exlog_idx]["user__id"] == user.id:
                log_table[exlogs[exlog_idx]["exercise_id"]] = exlogs[exlog_idx]
                exlog_idx += 1

            context["students"].append({  # this could be DRYer
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "name": user.get_name(),
                "id": user.id,
                "exercise_logs": log_table,
            })

    elif report_type == "video":
        # Fill in videos
        context["videos"] = get_topic_videos(topic_id=topic_id)

        # More code, but much faster
        video_ids = [vid["youtube_id"] for vid in context["videos"]]
        # Get students
        context["students"] = []
        vidlogs = VideoLog.objects \
            .filter(user__in=users, youtube_id__in=video_ids) \
            .order_by("user__last_name", "user__first_name")\
            .values("user__id", "complete", "youtube_id", "total_seconds_watched", "points")
        vidlogs = list(vidlogs)  # force the query to be executed now

        vidlog_idx = 0
        for user in users:
            log_table = {}
            while vidlog_idx < len(vidlogs) and vidlogs[vidlog_idx]["user__id"] == user.id:
                log_table[vidlogs[vidlog_idx]["youtube_id"]] = vidlogs[vidlog_idx]
                vidlog_idx += 1

            context["students"].append({  # this could be DRYer
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "name": user.get_name(),
                "id": user.id,
                "video_logs": log_table,
            })

    else:
        raise Http404("Unknown report_type: %s" % report_type)

    if "facility_user" in request.session:
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.debug("Failed to update Teacher userlog activity login: %s" % e)

    return context
