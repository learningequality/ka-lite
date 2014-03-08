"""
Views accessible as an API endpoint.  All should return JsonResponses.

Here, these are focused on:
* GET/save student progress (video, exercise)
* topic tree views (search, knowledge map)
"""
import cgi
import copy
import json
import os
import re
import os
import datetime
from annoying.functions import get_object_or_None
from functools import partial

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

from . import topic_tools
from .api_forms import ExerciseLogForm, VideoLogForm
from .models import VideoLog, ExerciseLog
from .topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes
from facility.models import FacilityGroup, FacilityUser
from fle_utils.general import break_into_chunks
from fle_utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessage, JsonResponseMessageError, JsonResponseMessageWarning
from fle_utils.internet.webcache import backend_cache_page
from fle_utils.mplayer_launcher import play_video_in_new_thread
from fle_utils.orderedset import OrderedSet
from i18n import lcode_to_ietf
from shared.decorators import require_admin
from testing.decorators import allow_api_profiling


class student_log_api(object):
    """
    Decorator (wrapper) for telling the user what happens
    in the case that they're not logged in (or other issues
    with using the API endpoint)
    """

    def __init__(self, logged_out_message):
        self.logged_out_message = logged_out_message

    def __call__(self, handler):
        @api_handle_error_with_json
        def wrapper_fn(request, *args, **kwargs):
            # TODO(bcipolli): send user info in the post data,
            #   allowing cross-checking of user information
            #   and better error reporting
            if "facility_user" not in request.session:
                return JsonResponseMessageWarning(self.logged_out_message + "  " + _("You must be logged in as a student or teacher to view/save progress."))
            else:
                return handler(request)
        return wrapper_fn


@student_log_api(logged_out_message=ugettext_lazy("Video progress not saved."))
def save_video_log(request):
    """
    Receives a video_id and relevant data,
    saves it to the currently authorized user.
    """

    # Form does all the data validation, including the video_id
    form = VideoLogForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        raise ValidationError(form.errors)
    data = form.data
    user = request.session["facility_user"]
    try:
        videolog = VideoLog.update_video_log(
            facility_user=user,
            video_id=data["video_id"],
            youtube_id=data["youtube_id"],
            current_position=data["current_position"],
            total_seconds_watched=data["total_seconds_watched"],  # don't set incrementally, to avoid concurrency issues
            points=data["points"],
            language=data.get("language") or request.language,
        )

    except ValidationError as e:
        return JsonResponseMessageError(_("Could not save VideoLog: %s") % e)

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed

    return JsonResponse({
        "points": videolog.points,
        "complete": videolog.complete,
        "messages": {},
    })


@student_log_api(logged_out_message=ugettext_lazy("Exercise progress not saved."))
def save_exercise_log(request):
    """
    Receives an exercise_id and relevant data,
    saves it to the currently authorized user.
    """

    # Form does all data validation, including of the exercise_id
    form = ExerciseLogForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        raise Exception(form.errors)
    data = form.data

    # More robust extraction of previous object
    user = request.session["facility_user"]
    (exerciselog, was_created) = ExerciseLog.get_or_initialize(user=user, exercise_id=data["exercise_id"])
    previously_complete = exerciselog.complete

    exerciselog.attempts = data["attempts"]  # don't increment, because we fail to save some requests
    exerciselog.streak_progress = data["streak_progress"]
    exerciselog.points = data["points"]
    exerciselog.language = data.get("language") or request.language

    try:
        exerciselog.full_clean()
        exerciselog.save()
    except ValidationError as e:
        return JsonResponseMessageError(_("Could not save ExerciseLog") + u": %s" % e)

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed

    # Special message if you've just completed.
    #   NOTE: it's important to check this AFTER calling save() above.
    if not previously_complete and exerciselog.complete:
        exercise = get_node_cache("Exercise").get(data["exercise_id"], [None])[0]
        junk, next_exercise = get_neighbor_nodes(exercise, neighbor_kind="Exercise") if exercise else None
        if next_exercise:
            return JsonResponse({"success": _("You have mastered this exercise!  Please continue on to <a href='%(href)s'>%(title)s</a>") % {
                "href": next_exercise["path"],
                "title": _(next_exercise["title"]),
            }})
        else:
            return JsonResponse({"success": _("You have mastered this exercise and this topic!")})

    # Return no message in release mode; "data saved" message in debug mode.
    return JsonResponse({})


@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Progress not loaded."))
def get_video_logs(request):
    """
    Given a list of video_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponseMessageError(_("Could not load VideoLog objects: Unrecognized input data format."))

    user = request.session["facility_user"]
    logs = VideoLog.objects \
        .filter(user=user, video_id__in=data) \
        .values("video_id", "complete", "total_seconds_watched", "points", "current_position")

    return JsonResponse(list(logs))


@allow_api_profiling
@student_log_api(logged_out_message=ugettext_lazy("Progress not loaded."))
def get_exercise_logs(request):
    """
    Given a list of exercise_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponseMessageError(_("Could not load ExerciseLog objects: Unrecognized input data format."))

    user = request.session["facility_user"]
    logs = ExerciseLog.objects \
            .filter(user=user, exercise_id__in=data) \
            .values("exercise_id", "streak_progress", "complete", "points", "struggling", "attempts")
    return JsonResponse(list(logs))



def _update_video_log_with_points(seconds_watched, video_id, video_length, youtube_id, facility_user, language):
    """Handle the callback from the mplayer thread, saving the VideoLog. """
    # TODO (bcipolli) add language info here

    if not facility_user:
        return  # in other places, we signal to the user that info isn't being saved, but can't do it here.
                #   adding this code for consistency / documentation purposes.

    new_points = VideoLog.calc_points(seconds_watched, video_length)

    videolog = VideoLog.update_video_log(
        facility_user=facility_user,
        video_id=video_id,
        youtube_id=youtube_id,
        additional_seconds_watched=seconds_watched,
        new_points=new_points,
        language=language,
    )

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed


@api_handle_error_with_json
@backend_cache_page
def flat_topic_tree(request, lang_code):
    return JsonResponse(get_flat_topic_tree(lang_code=lang_code))


@api_handle_error_with_json
@backend_cache_page
def knowledge_map_json(request, topic_id):
    """
    Topic nodes can now have a "knowledge_map" stamped on them.
    This code currently exposes that data to the kmap-editor code,
    mostly as it expects it now.

    So this is kind of a hack-ish mix of code that avoids rewriting kmap-editor.js,
    but allows a cleaner rewrite of the stored data, and bridges the gap between
    that messiness and the cleaner back-end.
    """

    # Try and get the requested topic, and make sure it has knowledge map data available.
    topic = topic_tools.get_node_cache("Topic").get(topic_id)
    if not topic:
        raise Http404("Topic '%s' not found" % topic_id)
    elif not "knowledge_map" in topic[0]:
        raise Http404("Topic '%s' has no knowledge map metadata." % topic_id)

    # For each node (can be of any type now), pull out only
    #   the relevant data.
    kmap = topic[0]["knowledge_map"]
    nodes_out = {}
    for id, kmap_data in kmap["nodes"].iteritems():
        cur_node = topic_tools.get_node_cache(kmap_data["kind"])[id][0]
        nodes_out[id] = {
            "id": cur_node["id"],
            "title": _(cur_node["title"]),
            "h_position":  kmap_data["h_position"],
            "v_position": kmap_data["v_position"],
            "icon_url": cur_node.get("icon_url", cur_node.get("icon_src")),  # messy
            "path": cur_node["path"],
        }
        if not "polylines" in kmap:  # messy
            # Two ways to define lines:
            # 1. have "polylines" defined explicitly
            # 2. use prerequisites to compute lines on the fly.
            nodes_out[id]["prerequisites"] = cur_node.get("prerequisites", [])

    return JsonResponse({
        "nodes": nodes_out,
        "polylines": kmap.get("polylines"),  # messy
    })
