import datetime
import re
import json
import sys
import logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial
from collections import OrderedDict

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils import simplejson
from django.utils.translation import ugettext as _

from coachreports.forms import DataForm
from config.models import Settings
from main import topicdata
from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.models import Facility, FacilityUser, FacilityGroup, DeviceZone, Device
from securesync.views import facility_required
from utils.decorators import api_handle_error_with_json
from utils.internet import StatusException, JsonResponse
from utils.topic_tools import get_topic_by_path


# Global variable of all the known stats, their internal and external names,
#    and their "datatype" (which is a value that Google Visualizations uses)
stats_dict = [
    {"key": "pct_mastery",        "name": _("% Mastery"),          "type": "number", "description": _("Percent of exercises mastered (at least 10 consecutive correct answers)")},
    {"key": "effort",             "name": _("% Effort"),           "type": "number", "description": _("Combination of attempts on exercises and videos watched.")},
    {"key": "ex:attempts",        "name": _("Average attempts"),   "type": "number", "description": _("Number of times submitting an answer to an exercise.")},
    {"key": "ex:streak_progress", "name": _("Average streak"),     "type": "number", "description": _("Maximum number of consecutive correct answers on an exercise.")},
    {"key": "ex:points",          "name": _("Exercise points"),    "type": "number", "description": _("[Pointless at the moment; tracks mastery linearly]")},
    { "key": "ex:completion_timestamp", "name": _("Time exercise completed"),"type": "datetime", "description": _("Day/time the exercise was completed.") },
    {"key": "vid:points",          "name": _("Video points"),      "type": "number", "description": _("Points earned while watching a video (750 max / video).")},
    { "key": "vid:total_seconds_watched","name": _("Video time"),   "type": "number", "description": _("Total seconds spent watching a video.") },
    { "key": "vid:completion_timestamp", "name": _("Time video completed"),"type": "datetime", "description": _("Day/time the video was completed.") },
]


def get_data_form(request, *args, **kwargs):
    """Get the basic data form, by combining information from
    keyword arguments and the request.REQUEST object.
    Along the way, check permissions to make sure whatever's being requested is OK.

    Request objects get priority over keyword args.
    """
    assert not args, "all non-request args should be keyword args"

    # Pull the form parameters out of the request or
    data = dict()
    # Default to empty string, as it makes template handling cleaner later.
    for field in ["facility", "group", "user", "xaxis", "yaxis"]:
        data[field] = request.REQUEST.get(field, kwargs.get(field, ""))
    data["topic_path"] = request.REQUEST.getlist("topic_path") or kwargs.get("topic_path", [])
    form = DataForm(data=data)

    # Filling in data for superusers
    if not "facility_user" in request.session:
        if request.user.is_superuser:
            if not (form.data["facility"] or form.data["group"] or form.data["user"]):
                facility = kwargs.get("facility")
                group = None if FacilityGroup.objects.all().count() != 1 else FacilityGroup.objects.all()[0]

                if group and not form.data["group"]:
                    form.data["group"] = group.id
                if facility and not form.data["facility"]:
                    form.data["facility"] = facility.id

    # Filling in data for FacilityUsers
    else:
        user = request.session["facility_user"]
        group = None if not user else user.group
        # Facility can come from user, facility
        facility = kwargs.get("facility") if not user else user.facility

        # Fill in default query data
        if not (form.data["facility"] or form.data["group"] or form.data["user"]):

            # Defaults:
            #   Students: only themselves
            #   Teachers: if nothing is specified, then show their group

            if request.is_admin:
                if group:
                    form.data["group"] = group.id
                elif facility:
                    form.data["facility"] = facility.id
                else:  # not a meaningful default, but responds efficiently (no data)
                    form.data["user"] = user.id
            else:
                form.data["user"] = user.id

        #
        # Authenticate
        if not request.is_admin:
            if group and form.data["group"] and group.id != form.data["group"]:  # can't go outside group
                # We could also redirect
                raise PermissionDenied("You cannot choose a group outside of your group.")
            elif facility and form.data["facility"] and facility.id != form.data["facility"]:
                # We could also redirect
                raise PermissionDenied("You cannot choose a facility outside of your own facility.")
            elif not request.is_admin:
                if not form.data["user"]:
                    # We could also redirect
                    raise PermissionDenied("You cannot choose facility/group-wide data.")
                elif user and form.data["user"] and user.id != form.data["user"]:
                    # We could also redirect
                    raise PermissionDenied("You cannot choose a user outside of yourself.")

    # Fill in backwards: a user implies a group
    if form.data.get("user") and not form.data.get("group"):
        user = get_object_or_404(FacilityUser, id=form.data["user"])
        form.data["group"] = getattr(user.group, "id", None)

    if form.data.get("group") and not form.data.get("facility"):
        group = get_object_or_404(FacilityGroup, id=form.data["group"])
        form.data["facility"] = getattr(group.facility, "id")

    return form


def query_logs(users, items, logtype, logdict):
    """
    Get a specified subset of logs for a particular set of users for either exercises or videos.
    users: list of users to query against.
    items: list of either exercises of videos to query.
    logtype: video or exercise - in future this could be expanded to query activity logs too.
    logdict: user keyed dictionary of logs (presumed to be empty by this code)
    """

    if logtype == "exercise":
        all_logs = ExerciseLog.objects.filter(user__in=users, exercise_id__in=items).values(
                        'user', 'complete', 'exercise_id', 'attempts', 'points', 'struggling', 'completion_timestamp', 'streak_progress').order_by('completion_timestamp')
    elif logtype == "video":
        all_logs = VideoLog.objects.filter(user__in=users, youtube_id__in=items).values(
            'user', 'complete', 'youtube_id', 'total_seconds_watched', 'completion_timestamp', 'points').order_by('completion_timestamp')
    else:
        raise Exception("Unknown log type: '%s'" % logtype)
    for log in all_logs:
        logdict[log['user']].append(log)
    return logdict


def compute_data(data_types, who, where):
    """
    Compute the data in "data_types" for each user in "who", for the topics selected by "where"

    who: list of users
    where: topic_path
    data_types can include:
        pct_mastery
        effort
        attempts
    """

    # None indicates that the data hasn't been queried yet.
    #   We'll query it on demand, for efficiency
    topics = None
    exercises = None
    videos = None

    # Initialize an empty dictionary of data, video logs, exercise logs, for each user
    data = OrderedDict(zip([w.id for w in who], [dict() for i in range(len(who))]))  # maintain the order of the users
    vid_logs = dict(zip([w.id for w in who], [[] for i in range(len(who))]))
    ex_logs = dict(zip([w.id for w in who], [[] for i in range(len(who))]))

    # Set up queries (but don't run them), so we have really easy aliases.
    #   Only do them if they haven't been done yet (tell this by passing in a value to the lambda function)
    # Topics: topics.
    # Exercises: names (ids for ExerciseLog objects)
    # Videos: youtube_id (ids for VideoLog objects)

    # This lambda partial creates a function to return all items with a particular path from the NODECACHE.
    search_fun_single_path = partial(lambda t, p: t["path"].startswith(p), p=tuple(where))
    # This lambda partial creates a function to return all items with paths matching a list of paths from NODECACHE.
    search_fun_multi_path = partial(lambda t, p: any([tp.startswith(p) for tp in t["paths"]]),  p=tuple(where))
    # Functions that use the functions defined above to return topics, exercises, and videos based on paths.
    query_topics = partial(lambda t, sf: t if t is not None else [t for t in filter(sf, topicdata.NODE_CACHE['Topic'].values())], sf=search_fun_single_path)
    query_exercises = partial(lambda e, sf: e if e is not None else [ex["name"] for ex in filter(sf, topicdata.NODE_CACHE['Exercise'].values())], sf=search_fun_multi_path)
    query_videos = partial(lambda v, sf: v if v is not None else [vid["youtube_id"] for vid in filter(sf, topicdata.NODE_CACHE['Video'].values())], sf=search_fun_multi_path)

    # No users, don't bother.
    if len(who) > 0:

        # Query out all exercises, videos, exercise logs, and video logs before looping to limit requests.
        # This means we could pull data for n-dimensional coach report displays with the same number of requests!
        exercises = query_exercises(exercises)

        ex_logs = query_logs(data.keys(), exercises, "exercise", ex_logs)

        videos = query_videos(videos)

        vid_logs = query_logs(data.keys(), videos, "video", vid_logs)

        for data_type in (data_types if not hasattr(data_types, "lower") else [data_types]):  # convert list from string, if necessary
            if data_type in data[data.keys()[0]]:  # if the first user has it, then all do; no need to calc again.
                continue

            #
            # These are summary stats: you only get one per user
            #
            if data_type == "pct_mastery":

                # Efficient query out, spread out to dict
                # ExerciseLog.filter(user__in=who, exercise_id__in=exercises).order_by("user.id")
                for user in data.keys():
                    data[user][data_type] = 0 if not ex_logs[user] else 100. * sum([el['complete'] for el in ex_logs[user]]) / float(len(exercises))

            elif data_type == "effort":
                if "ex:attempts" in data[data.keys()[0]] and "vid:total_seconds_watched" in data[data.keys()[0]]:
                    # exercises and videos would be initialized already
                    for user in data.keys():
                        avg_attempts = 0 if len(exercises) == 0 else sum(data[user]["ex:attempts"].values()) / float(len(exercises))
                        avg_video_points = 0 if len(videos) == 0 else sum(data[user]["vid:total_seconds_watched"].values()) / float(len(videos))
                        data[user][data_type] = 100. * (0.5 * avg_attempts / 10. + 0.5 * avg_video_points / 750.)
                else:
                    data_types += ["ex:attempts", "vid:total_seconds_watched", "effort"]

            #
            # These are detail stats: you get many per user
            #
            # Just querying out data directly: Video
            elif data_type.startswith("vid:") and data_type[4:] in [f.name for f in VideoLog._meta.fields]:

                for user in data.keys():
                    data[user][data_type] = OrderedDict([(v['youtube_id'], v[data_type[4:]]) for v in vid_logs[user]])

            # Just querying out data directly: Exercise
            elif data_type.startswith("ex:") and data_type[3:] in [f.name for f in ExerciseLog._meta.fields]:

                for user in data.keys():
                    data[user][data_type] = OrderedDict([(el['exercise_id'], el[data_type[3:]]) for el in ex_logs[user]])

            # Unknown requested quantity
            else:
                raise Exception("Unknown type: '%s' not in %s" % (data_type, str([f.name for f in ExerciseLog._meta.fields])))

    # Returning empty list instead of None allows javascript on client
    # side to read 'length' property without error.
    exercises = exercises or []

    videos = videos or []

    return {
        "data": data,
        "topics": topics,
        "exercises": exercises,
        "videos": videos,
    }


def convert_topic_tree_for_dynatree(node, level=0):
    """Converts topic tree from standard dictionary nodes
    to dictionary nodes usable by the dynatree app"""

    if node["kind"] == "Topic":
        if "Exercise" not in node["contains"]:
            return None
        children = []
        for child_node in node["children"]:
            child = convert_topic_tree_for_dynatree(child_node, level=level + 1)
            if child:
                children.append(child)

        return {
            "title": node["title"],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "isFolder": True,
            "key": node["path"],
            "children": children,
            "expand": level < 1,
        }
    return None


# view endpoints #######

@api_handle_error_with_json
def get_topic_tree(request, topic_path):
    return JsonResponse(convert_topic_tree_for_dynatree(get_topic_by_path(topic_path)));


@csrf_exempt
@api_handle_error_with_json
def api_data(request, xaxis="", yaxis=""):
    """Request contains information about what data are requested (who, what, and how).

    Response should be a JSON object
    * data contains the data, structred by user and then datatype
    * the rest of the data is metadata, useful for displaying detailed info about data.
    """

    # Get the request form
    form = get_data_form(request, xaxis=xaxis, yaxis=yaxis)  # (data=request.REQUEST)

    # Query out the data: who?
    if form.data.get("user"):
        facility = []
        groups = []
        users = [get_object_or_404(FacilityUser, id=form.data.get("user"))]
    elif form.data.get("group"):
        facility = []
        groups = [get_object_or_404(FacilityGroup, id=form.data.get("group"))]
        users = FacilityUser.objects.filter(group=form.data.get("group"), is_teacher=False).order_by("last_name", "first_name")
    elif form.data.get("facility"):
        facility = get_object_or_404(Facility, id=form.data.get("facility"))
        groups = FacilityGroup.objects.filter(facility__in=[form.data.get("facility")])
        users = FacilityUser.objects.filter(facility__in=[form.data.get("facility")], is_teacher=False).order_by("last_name", "first_name")
    else:
        return HttpResponseNotFound("Did not specify facility, group, nor user.")

    # Query out the data: where?
    if not form.data.get("topic_path"):
        return HttpResponseNotFound("Must specify a topic path")

    # Query out the data: what?
    try:
        computed_data = compute_data(data_types=[form.data.get("xaxis"), form.data.get("yaxis")], who=users, where=form.data.get("topic_path"))
        json_data = {
            "data": computed_data["data"],
            "exercises": computed_data["exercises"],
            "videos": computed_data["videos"],
            "users": dict(zip([u.id for u in users],
                                ["%s, %s" % (u.last_name, u.first_name) for u in users]
                         )),
            "groups":  dict(zip([g.id for g in groups],
                                 dict(zip(["id", "name"], [(g.id, g.name) for g in groups])),
                          )),
            "facility": None if not facility else {
                "name": facility.name,
                "id": facility.id,
            }
        }

        # Now we have data, stream it back with a handler for date-times
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        return HttpResponse(content=json.dumps(json_data, default=dthandler), content_type="application/json")

    except Exception as e:
        return HttpResponseServerError(str(e))
