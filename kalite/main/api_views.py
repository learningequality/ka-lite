import re, json
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils import simplejson
from django.db.models import Max
from annoying.functions import get_object_or_None
import settings
from settings import slug_key, title_key
from main import topicdata
from utils.jobs import force_job
from models import FacilityUser, VideoLog, ExerciseLog, VideoFile

def require_admin(handler):
    def wrapper_fn(request, *args, **kwargs):
        if not request.is_admin:
            return HttpResponseNotAllowed("This path is only available to admins.")
        return handler(request, *args, **kwargs)
    return wrapper_fn

class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str) and not isinstance(content, unicode):
            content = simplejson.dumps(content, indent=2, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


def save_video_log(request):
    if "facility_user" not in request.session:
        return JsonResponse({})
    data = simplejson.loads(request.raw_post_data or "{}")
    videolog = VideoLog()
    videolog.user = request.session["facility_user"]
    videolog.youtube_id = data.get("youtube_id", "")
    old_videolog = videolog.get_existing_instance() or VideoLog()
    videolog.total_seconds_watched = old_videolog.total_seconds_watched + data.get("seconds_watched", 0)
    videolog.complete = old_videolog.complete or data.get("complete", False)
    videolog.points = max(old_videolog.points, data.get("points", None)) or None
    try:
        videolog.full_clean()
        videolog.save()
        return JsonResponse({
            "points": videolog.points,
            "complete": videolog.complete,
        })
    except ValidationError as e:
        return JsonResponse({"error": "Could not save VideoLog: %s" % e}, status=500)


def save_exercise_log(request):
    if "facility_user" not in request.session:
        return JsonResponse({})
    data = simplejson.loads(request.raw_post_data or "{}")
    exerciselog = ExerciseLog()
    exerciselog.user = request.session["facility_user"]
    exerciselog.exercise_id = data.get("exercise_id", "")
    old_exerciselog = exerciselog.get_existing_instance() or ExerciseLog()
    exerciselog.attempts = old_exerciselog.attempts + 1
    exerciselog.streak_progress = data.get("streak_progress", None)
    try:
        exerciselog.full_clean()
        exerciselog.save()
        return JsonResponse({})
    except ValidationError as e:
        return JsonResponse({"error": "Could not save ExerciseLog: %s" % e}, status=500)


def get_video_logs(request):
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse([])
    if "facility_user" not in request.session:
        return JsonResponse([])
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


def get_exercise_logs(request):
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data, list):
        return JsonResponse([])
    if "facility_user" not in request.session:
        return JsonResponse([])
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
        exerciselog = ExerciseLog.objects.filter(user=user, exercise_id=exercise_id).latest("counter")
    except ExerciseLog.DoesNotExist:
        return {}
    return {
        "exercise_id": exercise_id,
        "streak_progress": exerciselog.streak_progress,
        "complete": exerciselog.streak_progress == 100,
    }

@require_admin
def start_video_download(request):
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    downloading_videos = VideoFile.objects.filter(flagged_for_download=True)
    priority = downloading_videos.aggregate(Max("priority")).get("priority__max", 0) or 0
    for id in youtube_ids:
        videofile = get_object_or_None(VideoFile, youtube_id=id) or VideoFile(youtube_id=id)
        if videofile.download_in_progress:
            continue
        priority += 1
        videofile.priority = priority
        videofile.flagged_for_download = True
        videofile.percent_complete = 0
        videofile.save()
    force_job("videodownload", "Download Videos")
    return JsonResponse({})

@require_admin
def check_video_download(request):
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    percentages = {}
    for id in youtube_ids:
        videofile = get_object_or_None(VideoFile, youtube_id=id) or VideoFile(youtube_id=id)
        percentages[id] = videofile.percent_complete
    return JsonResponse(percentages)

def get_video_download_status(youtube_id):
    videofile = get_object_or_None(VideoFile, youtube_id=youtube_id)
    if not videofile:
        return "unstarted"
    if videofile.percent_complete == 0 and not videofile.download_in_progress:
        return "unstarted"
    if videofile.percent_complete == 100 and not videofile.download_in_progress:
        return "complete"
    else:
        return "partial"

@require_admin
def get_video_download_list(request):
    videofiles = VideoFile.objects.filter(flagged_for_download=True).values("youtube_id")
    video_ids = [video["youtube_id"] for video in videofiles]
    return JsonResponse(video_ids)

def convert_topic_tree(node, level=0):
    if node["kind"] == "Topic":
        if "Video" not in node["contains"]:
            return None
        children = []
        unstarted = True
        complete = True
        for child_node in node["children"]:
            child = convert_topic_tree(child_node, level+1)
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
            "title": node[title_key["Topic"]],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "isFolder": True,
            "key": node[slug_key["Topic"]],
            "children": children,
            "addClass": complete and "complete" or unstarted and "unstarted" or "partial",
            "expand": level < 1,
        }
    if node["kind"] == "Video":
        return {
            "title": node[title_key["Video"]],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "key": node["youtube_id"],
            "addClass": get_video_download_status(node["youtube_id"]),
        }
    return None

@require_admin
def get_topic_tree(request):
    return JsonResponse(convert_topic_tree(topicdata.TOPICS))

@require_admin
def get_group_data(request):
    data = simplejson.loads(request.raw_post_data or "[]")
    if not isinstance(data["exercises"], list):
        return JsonResponse([])
    if "facility_user" not in request.session:
        return JsonResponse([])
    group = data["group"]
    exercise_ids = data["exercises"]
    users = []
    if group:
        users = FacilityUser.objects.filter(group = group)
    group_responses = {}
    for user in users:
        responses = []
        for exercise_id in exercise_ids:
            response = _get_exercise_log_dict(request, user, exercise_id)
            if response:
                responses.append(response)
        group_responses[user] = responses
    return JsonResponse(group_responses)