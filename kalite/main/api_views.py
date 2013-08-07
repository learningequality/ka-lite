import json
import re
from annoying.functions import get_object_or_None

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.translation import ugettext as _

import settings
from .api_forms import ExerciseLogForm, VideoLogForm
from .models import FacilityUser, VideoLog, ExerciseLog, VideoFile
from config.models import Settings
from main import topicdata
from securesync.models import FacilityGroup
from shared.caching import invalidate_all_pages_related_to_video
from utils.jobs import force_job, job_status
from utils.videos import delete_downloaded_files
from utils.decorators import require_admin
from utils.general import break_into_chunks
from utils.internet import JsonResponse
from utils.orderedset import OrderedSet
from utils.decorators import api_handle_error_with_json


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
                return JsonResponse({"warning": self.logged_out_message + "  " + _("You must be logged in as a facility user to view/save progress.")}, status=500)
            else:
                return handler(request)
        return wrapper_fn


@student_log_api(logged_out_message=_("Video progress not saved."))
def save_video_log(request):
    """
    Receives a youtube_id and relevant data,
    saves it to the currently authorized user.
    """

    # Form does all the data validation, including the youtube_id
    form = VideoLogForm(data=simplejson.loads(request.raw_post_data))
    if not form.is_valid():
        raise ValidationError(form.errors)
    data = form.data

    # More robust extraction of previous object
    videolog = get_object_or_None(VideoLog, user=request.session["facility_user"], youtube_id=data["youtube_id"])
    videolog = videolog or VideoLog(user=request.session["facility_user"], youtube_id=data["youtube_id"])

    videolog.total_seconds_watched  += data["seconds_watched"]
    videolog.points = max(videolog.points, data["points"])  # videolog.points cannot be None

    try:
        videolog.full_clean()
        videolog.save()
    except ValidationError as e:
        return JsonResponse({"error": "Could not save VideoLog: %s" % e}, status=500)

    return JsonResponse({
        "points": videolog.points,
        "complete": videolog.complete,
        "messages": {} if not settings.DEBUG else { "success": "Video data saved." },
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
    exerciselog = get_object_or_None(ExerciseLog, user=request.session["facility_user"], exercise_id=data["exercise_id"])
    exerciselog = exerciselog or ExerciseLog(user=request.session["facility_user"], exercise_id=data["exercise_id"])
    previously_complete = exerciselog.complete

    exerciselog.attempts += 1
    exerciselog.streak_progress = data["streak_progress"]
    exerciselog.points = data["points"]

    try:
        exerciselog.full_clean()
        exerciselog.save()
    except ValidationError as e:
        return JsonResponse({"error": "Could not save ExerciseLog: %s" % e}, status=500)

    # Special message if you've just completed.
    #   NOTE: it's important to check this AFTER calling save() above.
    if not previously_complete and exerciselog.complete:
        return JsonResponse({"success": _("You've mastered this exercise!")})
    
    # Return no message in release mode; "data saved" message in debug mode.
    return JsonResponse({} if not settings.DEBUG else {"success": "data saved."})


@student_log_api(logged_out_message=_("Progress not loaded."))
def get_video_logs(request):
    """
    Given a list of youtube_ids, retrieve a list of video logs for this user.
    """

    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse({"error": "Could not load VideoLog objects: Unrecognized input data format." % e}, status=500)

    user = request.session["facility_user"]
    responses = []
    for youtube_id in data:
        response = _get_video_log_dict(request, user, youtube_id)
        if response:
            responses.append(response)
    return JsonResponse(responses)


def _get_video_log_dict(request, user, youtube_id):
    if not youtube_id:
        return {}
    try:
        videolog = VideoLog.objects.filter(user=user, youtube_id=youtube_id).latest("counter")
    except VideoLog.DoesNotExist:
        return {}
    return {
        "youtube_id": youtube_id,
        "total_seconds_watched": videolog.total_seconds_watched,
        "complete": videolog.complete,
        "points": videolog.points,
    }


@student_log_api(logged_out_message=_("Progress not loaded."))
def get_exercise_logs(request):
    """
    Given a list of exercise_ids, retrieve a list of video logs for this user.
    """

    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse({"error": "Could not load ExerciseLog objects: Unrecognized input data format." % e}, status=500)

    user = request.session["facility_user"]
    responses = []
    for exercise_id in data:
        response = _get_exercise_log_dict(request, user, exercise_id)
        if response:
            responses.append(response)
    return JsonResponse(responses)


def _get_exercise_log_dict(request, user, exercise_id):
    if not exercise_id:
        return {}
    try:
        exerciselog = ExerciseLog.objects.get(user=user, exercise_id=exercise_id)
    except ExerciseLog.DoesNotExist:
        return {}
    return {
        "exercise_id": exercise_id,
        "streak_progress": exerciselog.streak_progress,
        "complete": exerciselog.complete,
        "points": exerciselog.points,
        "struggling": exerciselog.struggling,
    }


@require_admin
@api_handle_error_with_json
def start_video_download(request):
    youtube_ids = OrderedSet(simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", []))

    video_files_to_create = [id for id in youtube_ids if not get_object_or_None(VideoFile, youtube_id=id)]
    video_files_to_update = youtube_ids - OrderedSet(video_files_to_create)

    VideoFile.objects.bulk_create([VideoFile(youtube_id=id, flagged_for_download=True) for id in video_files_to_create])

    for chunk in break_into_chunks(youtube_ids):
        video_files_needing_model_update = VideoFile.objects.filter(download_in_progress=False, youtube_id__in=chunk).exclude(percent_complete=100)
        video_files_needing_model_update.update(percent_complete=0, cancel_download=False, flagged_for_download=True)

    force_job("videodownload", "Download Videos")
    return JsonResponse({})

@require_admin
@api_handle_error_with_json
def delete_videos(request):
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    for id in youtube_ids:
        # Delete the file on disk
        delete_downloaded_files(id)

        # Delete the file in the database
        videofile = get_object_or_None(VideoFile, youtube_id=id)
        if videofile:
            videofile.cancel_download = True
            videofile.flagged_for_download = False
            videofile.flagged_for_subtitle_download = False
            videofile.save()

        # Refresh the cache
        invalidate_all_pages_related_to_video(video_id=id)

    return JsonResponse({})

@require_admin
@api_handle_error_with_json
def check_video_download(request):
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    percentages = {}
    percentages["downloading"] = job_status("videodownload")
    for id in youtube_ids:
        videofile = get_object_or_None(VideoFile, youtube_id=id) or VideoFile(youtube_id=id)
        percentages[id] = videofile.percent_complete
    return JsonResponse(percentages)

@require_admin
@api_handle_error_with_json
def get_video_download_list(request):
    videofiles = VideoFile.objects.filter(flagged_for_download=True).values("youtube_id")
    video_ids = [video["youtube_id"] for video in videofiles]
    return JsonResponse(video_ids)

@require_admin
@api_handle_error_with_json
def start_subtitle_download(request):
    new_only = simplejson.loads(request.raw_post_data or "{}").get("new_only", False)
    language = simplejson.loads(request.raw_post_data or "{}").get("language", "")
    language_list = topicdata.LANGUAGE_LIST
    current_language = Settings.get("subtitle_language")
    new_only = new_only and (current_language == language)
    if language in language_list:
        Settings.set("subtitle_language", language)
    else:
        return JsonResponse({"error": "This language is not currently supported - please update the language list"}, status=500)
    if new_only:
        videofiles = VideoFile.objects.filter(Q(percent_complete=100) | Q(flagged_for_download=True), subtitles_downloaded=False)
    else:
        videofiles = VideoFile.objects.filter(Q(percent_complete=100) | Q(flagged_for_download=True))
    for videofile in videofiles:
        videofile.cancel_download = False
        if videofile.subtitle_download_in_progress:
            continue
        videofile.flagged_for_subtitle_download = True
        if not new_only:
            videofile.subtitles_downloaded = False
        videofile.save()
    force_job("subtitledownload", "Download Subtitles")
    return JsonResponse({})

@require_admin
@api_handle_error_with_json
def check_subtitle_download(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True)
    return JsonResponse(videofiles.count())

@require_admin
@api_handle_error_with_json
def get_subtitle_download_list(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True).values("youtube_id")
    video_ids = [video["youtube_id"] for video in videofiles]
    return JsonResponse(video_ids)

@require_admin
@api_handle_error_with_json
def cancel_downloads(request):

    # clear all download in progress flags, to make sure new downloads will go through
    VideoFile.objects.all().update(download_in_progress=False)

    # unflag all video downloads
    VideoFile.objects.filter(flagged_for_download=True).update(cancel_download=True, flagged_for_download=False)

    # unflag all subtitle downloads
    VideoFile.objects.filter(flagged_for_subtitle_download=True).update(cancel_download=True, flagged_for_subtitle_download=False)

    force_job("videodownload", stop=True)
    force_job("subtitledownload", stop=True)

    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def remove_from_group(request):
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

def annotate_topic_tree(node, level=0, statusdict=None):
    if not statusdict:
        statusdict = {}
    if node["kind"] == "Topic":
        if "Video" not in node["contains"]:
            return None
        children = []
        unstarted = True
        complete = True
        for child_node in node["children"]:
            child = annotate_topic_tree(child_node, level=level+1, statusdict=statusdict)
            if child:
                if child["addClass"] == "unstarted":
                    complete = False
                if child["addClass"] == "partial":
                    complete = False
                    unstarted = False
                if child["addClass"] == "complete":
                    unstarted = False
                children.append(child)
        return {
            "title": node["title"],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "isFolder": True,
            "key": node["slug"],
            "children": children,
            "addClass": complete and "complete" or unstarted and "unstarted" or "partial",
            "expand": level < 1,
        }
    if node["kind"] == "Video":
        #statusdict contains an item for each video registered in the database
        # will be {} (empty dict) if there are no videos downloaded yet
        percent = statusdict.get(node["youtube_id"], 0)
        if not percent:
            status = "unstarted"
        elif percent == 100:
            status = "complete"
        else:
            status = "partial"
        return {
            "title": node["title"],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "key": node["youtube_id"],
            "addClass": status,
        }
    return None

#@require_admin
def get_annotated_topic_tree():
    statusdict = dict(VideoFile.objects.values_list("youtube_id", "percent_complete"))
    return annotate_topic_tree(topicdata.TOPICS, statusdict=statusdict)

@require_admin
@api_handle_error_with_json
def get_topic_tree(request):
    return JsonResponse(get_annotated_topic_tree())
