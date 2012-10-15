import re, json
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils import simplejson

from models import FacilityUser, VideoLog, ExerciseLog


class JsonResponse(HttpResponse):
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str):
            content = simplejson.dumps(content, indent=2, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)


def save_video_log(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    videolog = VideoLog()
    if "facility_user" in request.session:
        videolog.user = request.session["facility_user"]
        videolog.total_seconds_watched = data.get("total_seconds_watched", 0)
    videolog.youtube_id = data.get("youtube_id", "")
    videolog.seconds_watched = data.get("seconds_watched", None)
    try:
        videolog.full_clean()
        videolog.save()
        return JsonResponse({})
    except ValidationError as e:
        return JsonResponse({"error": "Could not save VideoLog: %s" % e}, status=500)


def save_exercise_log(request):
    data = simplejson.loads(request.raw_post_data or "{}")
    exerciselog = ExerciseLog()
    if "facility_user" in request.session:
        exerciselog.user = request.session["facility_user"]
    exerciselog.exercise_id = data.get("exercise_id", "")
    exerciselog.answer = data.get("answer", "")
    exerciselog.correct = data.get("correct", "")
    exerciselog.seed = data.get("seed", None)
    exerciselog.hints_used = data.get("hints_used", None)
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
