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
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.safestring import SafeString, SafeUnicode, mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.gzip import gzip_page

import settings
import version
from .api_forms import ExerciseLogForm, VideoLogForm, DateTimeForm
from .models import VideoLog, ExerciseLog
from config.models import Settings
from securesync.models import FacilityGroup, FacilityUser
from shared.caching import backend_cache_page
from shared.decorators import allow_api_profiling, require_admin
from shared.jobs import force_job, job_status
from shared.topic_tools import get_flat_topic_tree
from shared.videos import delete_downloaded_files
from utils.general import break_into_chunks
from utils.internet import api_handle_error_with_json, JsonResponse
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
                return JsonResponse({"warning": self.logged_out_message + "  " + _("You must be logged in as a student or teacher to view/save progress.")}, status=500)
            else:
                return handler(request)
        return wrapper_fn


@student_log_api(logged_out_message=_("Video progress not saved."))
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
        return JsonResponse({"error": "Could not save VideoLog: %s" % e}, status=500)

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed

    return JsonResponse({
        "points": videolog.points,
        "complete": videolog.complete,
        "messages": {},
    })


@student_log_api(logged_out_message=_("Exercise progress not saved."))
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
        return JsonResponse({"error": _("Could not save ExerciseLog") + u": %s" % e}, status=500)

    if "points" in request.session:
        del request.session["points"]  # will be recomputed when needed

    # Special message if you've just completed.
    #   NOTE: it's important to check this AFTER calling save() above.
    if not previously_complete and exerciselog.complete:
        return JsonResponse({"success": _("You have mastered this exercise!")})

    # Return no message in release mode; "data saved" message in debug mode.
    return JsonResponse({})


@allow_api_profiling
@student_log_api(logged_out_message=_("Progress not loaded."))
def get_video_logs(request):
    """
    Given a list of video_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse({"error": "Could not load VideoLog objects: Unrecognized input data format." % e}, status=500)

    user = request.session["facility_user"]
    logs = VideoLog.objects \
        .filter(user=user, video_id__in=data) \
        .values("video_id", "complete", "total_seconds_watched", "points")

    return JsonResponse(list(logs))


@allow_api_profiling
@student_log_api(logged_out_message=_("Progress not loaded."))
def get_exercise_logs(request):
    """
    Given a list of exercise_ids, retrieve a list of video logs for this user.
    """
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse({"error": "Could not load ExerciseLog objects: Unrecognized input data format." % e}, status=500)

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
        return JsonResponse({"error": _("This can only be done on Raspberry Pi systems")}, status=403)

    # Form does all the data validation - including ensuring that the data passed is a proper date time.
    # This is necessary to prevent arbitrary code being run on the system.
    form = DateTimeForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        return JsonResponse({"error": _("Could not read date and time: Unrecognized input data format.")}, status=500)

    try:

        if os.system('sudo date +%%F%%T -s "%s"' % form.data["date_time"]):
            raise PermissionDenied

    except PermissionDenied as e:
        return JsonResponse({"error": _("System permissions prevented time setting, please run with root permissions")}, status=500)

    now = datetime.datetime.now().isoformat(" ").split(".")[0]

    return JsonResponse({"success": _("System time was reset successfully; current system time: %s" % now)})


# Functions below here focused on users

@require_admin
@api_handle_error_with_json
def remove_from_group(request):
    """
    API endpoint for removing users from group
    (from user management page)
    """
    users = simplejson.loads(request.raw_post_data or "{}").get("users", "")
    users_to_remove = FacilityUser.objects.filter(username__in=users)
    users_to_remove.update(group=None)
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def move_to_group(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    group = simplejson.loads(request.raw_post_data or "{}").get("group", "")
    group_update = FacilityGroup.objects.get(pk=group)
    users_to_move = FacilityUser.objects.filter(username__in=users)
    users_to_move.update(group=group_update)
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def delete_users(request):
    users = simplejson.loads(request.raw_post_data or "{}").get("users", [])
    users_to_delete = FacilityUser.objects.filter(username__in=users)
    users_to_delete.delete()
    return JsonResponse({})


@api_handle_error_with_json
def launch_mplayer(request):
    """
    Launch an mplayer instance in a new thread, to play the video requested via the API.
    """

    if not settings.USE_MPLAYER:
        raise PermissionDenied("You can only initiate mplayer if USE_MPLAYER is set to True.")

    if "youtube_id" not in request.REQUEST:
        return JsonResponse({"error": "no youtube_id specified"}, status=500)

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
        "current_language": request.session["django_language"],
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

    if lang_code != request.session.get("django_language"):
        raise NotImplementedError(_("Currently, only retrieving the flat topic tree in the user's currently selected language is supported (current=%(current_lang)s, requested=%(requested_lang)s).") % {
            "current_lang": request.session.get("django_language"),
            "requested_lang": lang_code,
        })
    return JsonResponse(get_flat_topic_tree(lang_code=lang_code))
