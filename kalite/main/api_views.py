import cgi
import copy
import json
import os
import re
import os
import datetime
from annoying.functions import get_object_or_None
from functools import partial

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

import settings
import version
from . import topicdata
from .api_forms import ExerciseLogForm, VideoLogForm, DateTimeForm
from .caching import backend_cache_page
from .models import VideoLog, ExerciseLog
from .topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes
from facility.models import FacilityGroup, FacilityUser
from i18n import lcode_to_ietf
from shared.decorators import require_admin
from testing.decorators import allow_api_profiling
from utils.general import break_into_chunks
from utils.internet import api_handle_error_with_json, JsonResponse, JsonResponseMessage, JsonResponseMessageError, JsonResponseMessageWarning
from utils.mplayer_launcher import play_video_in_new_thread
from utils.orderedset import OrderedSet


class student_log_api(object):

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
        .values("video_id", "complete", "total_seconds_watched", "points")

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


@require_admin
@api_handle_error_with_json
def time_set(request):
    """
    Receives a date-time string and sets the system date-time
    RPi only.
    """

    if not settings.ENABLE_CLOCK_SET:
        return JsonResponseMessageError(_("This can only be done on Raspberry Pi systems"), status=403)

    # Form does all the data validation - including ensuring that the data passed is a proper date time.
    # This is necessary to prevent arbitrary code being run on the system.
    form = DateTimeForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        return JsonResponseMessageError(_("Could not read date and time: Unrecognized input data format."))

    try:

        if os.system('sudo date +%%F%%T -s "%s"' % form.data["date_time"]):
            raise PermissionDenied

    except PermissionDenied as e:
        return JsonResponseMessageError(_("System permissions prevented time setting, please run with root permissions"))

    now = datetime.datetime.now().isoformat(" ").split(".")[0]

    return JsonResponseMessage(_("System time was reset successfully; current system time: %s") % now)


# Functions below here focused on users


@api_handle_error_with_json
def launch_mplayer(request):
    """
    Launch an mplayer instance in a new thread, to play the video requested via the API.
    """

    if not settings.USE_MPLAYER:
        raise PermissionDenied("You can only initiate mplayer if USE_MPLAYER is set to True.")

    if "youtube_id" not in request.REQUEST:
        return JsonResponseMessageError(_("No youtube_id specified"))

    youtube_id = request.REQUEST["youtube_id"]
    video_id = request.REQUEST["video_id"]
    facility_user = request.session.get("facility_user")

    callback = partial(
        _update_video_log_with_points,
        video_id=video_id,
        youtube_id=youtube_id,
        facility_user=facility_user,
        language=request.language,
    )

    play_video_in_new_thread(youtube_id, content_root=settings.CONTENT_ROOT, callback=callback)

    return JsonResponse({})


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


def compute_total_points(user):
    if user.is_teacher:
        return None
    else:
        return VideoLog.get_points_for_user(user) + ExerciseLog.get_points_for_user(user)


# On pages with no forms, we want to ensure that the CSRF cookie is set, so that AJAX POST
# requests will be possible. Since `status` is always loaded, it's a good place for this.
@ensure_csrf_cookie
@allow_api_profiling
@api_handle_error_with_json
def status(request):
    """In order to promote (efficient) caching on (low-powered)
    distributed devices, we do not include ANY user data in our
    templates.  Instead, an AJAX request is made to download user
    data, and javascript used to update the page.

    This view is the view providing the json blob of user information,
    for each page view on the distributed server.

    Besides basic user data, we also provide access to the
    Django message system through this API, again to promote
    caching by excluding any dynamic information from the server-generated
    templates.
    """
    # Build a list of messages to pass to the user.
    #   Iterating over the messages removes them from the
    #   session storage, thus they only appear once.
    message_dicts = []
    for message in get_messages(request):
        # Make sure to escape strings not marked as safe.
        # Note: this duplicates a bit of Django template logic.
        msg_txt = message.message
        if not (isinstance(msg_txt, SafeString) or isinstance(msg_txt, SafeUnicode)):
            msg_txt = cgi.escape(unicode(msg_txt))

        message_dicts.append({
            "tags": message.tags,
            "text": msg_txt,
        })

    # Default data
    data = {
        "is_logged_in": request.is_logged_in,
        "registered": request.session["registered"],
        "is_admin": request.is_admin,
        "is_django_user": request.is_django_user,
        "points": 0,
        "current_language": request.session[settings.LANGUAGE_COOKIE_NAME],
        "messages": message_dicts,
    }
    # Override properties using facility data
    if "facility_user" in request.session:  # Facility user
        user = request.session["facility_user"]
        data["is_logged_in"] = True
        data["username"] = user.get_name()
        if "points" not in request.session:
            request.session["points"] = compute_total_points(user)
        data["points"] = request.session["points"]
    # Override data using django data
    if request.user.is_authenticated():  # Django user
        data["is_logged_in"] = True
        data["username"] = request.user.username

    return JsonResponse(data)


def getpid(request):
    #who am I?  return the PID; used to kill the webserver process if the PID file is missing
    try:
        return HttpResponse(os.getpid())
    except:
        return HttpResponse("")


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
    topic = topicdata.NODE_CACHE["Topic"].get(topic_id)
    if not topic:
        raise Http404("Topic '%s' not found" % topic_id)
    elif not "knowledge_map" in topic[0]:
        raise Http404("Topic '%s' has no knowledge map metadata." % topic_id)

    # For each node (can be of any type now), pull out only
    #   the relevant data.
    kmap = topic[0]["knowledge_map"]
    nodes_out = {}
    for id, kmap_data in kmap["nodes"].iteritems():
        cur_node = topicdata.NODE_CACHE[kmap_data["kind"]][id][0]
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
