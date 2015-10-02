from math import ceil
import datetime

from django.utils.translation import ugettext as _
from django.db.models import Q, Sum, Avg

from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError

from kalite.main.models import ExerciseLog, VideoLog, ContentLog, AttemptLog, UserLogSummary
from kalite.facility.models import FacilityUser
from kalite.shared.decorators.auth import require_admin
from kalite.topic_tools import get_topic_leaves, get_exercise_cache, get_content_cache

def get_learners_from_GET(request):
    learner_ids = request.GET.getlist("user_id")

    group_ids = request.GET.getlist("group_id")

    facility_ids = request.GET.getlist("facility_id")

    # Restrict filtering based on specificity. Use most specific filter (learner_ids, group_ids, facility_ids).

    if learner_ids:
        learner_filter = Q(pk__in=learner_ids)
    elif group_ids:
        if "Ungrouped" in group_ids and facility_ids:
            learner_filter = (Q(group__pk__in=group_ids) | Q(group__isnull=True)) & Q(facility__pk__in=facility_ids)
        else:
            learner_filter = Q(group__pk__in=group_ids)
    else:
        # Do this to ensure that we never return more than one facility's worth of anything.
        learner_filter = Q(facility__pk__in=facility_ids)

    return FacilityUser.objects.filter(learner_filter & Q(is_teacher=False)).order_by("last_name")

def return_log_type_details(log_type, topic_ids=None):
    fields = ["user", "points", "complete", "completion_timestamp", "completion_counter"]
    if log_type == "exercise":
        LogModel = ExerciseLog
        fields.extend(["exercise_id", "attempts", "struggling", "streak_progress", "attempts_before_completion"])
        obj_id_field = "exercise_id__in"
    elif log_type == "video":
        LogModel = VideoLog
        fields.extend(["video_id", "total_seconds_watched"])
        obj_id_field = "video_id__in"
    elif log_type == "content":
        LogModel = ContentLog
        fields.extend(["content_id", "progress"])
        obj_id_field = "content_id__in"
    else:
        return None
    id_field = obj_id_field.split("__")[0]
    if topic_ids:
        objects = [obj for topic_id in topic_ids for obj in get_topic_leaves(topic_id=topic_id, leaf_type=log_type.title())]
        obj_ids = {obj_id_field: [obj.get("id") for obj in objects]}
    else:
        objects = []
        obj_ids = {}
    return LogModel, fields, id_field, obj_ids, objects

@require_admin
def learner_logs(request):

    page = request.GET.get("page", 1)

    limit = request.GET.get("limit", 50)

    # Look back a week by default
    time_window = request.GET.get("time_window", 7)

    start_date = request.GET.get("start_date", None)

    end_date = request.GET.get("end_date", None)

    topic_ids = request.GET.getlist("topic_id", [])

    learners = get_learners_from_GET(request)

    pages = int(ceil(len(learners)/float(limit)))

    if page*limit < len(learners):

        learners = learners[(page - 1)*limit: page*limit]

    log_types = request.GET.getlist("log_type", ["exercise", "video", "content"])

    output_logs = []

    output_objects = []

    end_date = datetime.datetime.strptime(end_date,'%Y/%m/%d') if end_date else datetime.datetime.now()

    start_date = datetime.datetime.strptime(start_date,'%Y/%m/%d') if start_date else end_date - datetime.timedelta(time_window)

    for log_type in log_types:
        LogModel, fields, id_field, obj_ids, objects = return_log_type_details(log_type, topic_ids)

        log_objects = LogModel.objects.filter(user__in=learners, **obj_ids).values(*fields)
        if not topic_ids:
            topic_objects = log_objects.filter(latest_activity_timestamp__gte=start_date, latest_activity_timestamp__lte=end_date)
            if topic_objects.count() == 0:
                topic_objects = log_objects
            objects = dict([(obj[id_field], get_content_cache().get(obj[id_field], get_exercise_cache().get(obj[id_field]))) for obj in topic_objects]).values()
        output_objects.extend(objects)
        output_logs.extend(log_objects)

    return JsonResponse({
        "logs": output_logs,
        "contents": output_objects,
        # Sometimes 'learners' gets collapsed to a list from the Queryset. This insures against that eventuality.
        "learners": [{
            "first_name": learner.first_name,
            "last_name": learner.last_name,
            "username": learner.username,
            "pk": learner.pk
            } for learner in learners],
        "page": page,
        "pages": pages,
        "limit": limit
    })

@require_admin
def aggregate_learner_logs(request):

    learners = get_learners_from_GET(request)

    event_limit = request.GET.get("event_limit", 10)

    # Look back a week by default
    time_window = request.GET.get("time_window", 7)

    start_date = request.GET.get("start_date", None)

    end_date = request.GET.get("end_date", None)

    topic_ids = request.GET.getlist("topic_id", [])

    log_types = request.GET.getlist("log_type", ["exercise", "video", "content"])

    output_logs = []

    output_dict = {
        "content_time_spent": 0,
        "exercise_attempts": 0,
        "exercise_mastery": None,
    }
    
    end_date = datetime.datetime.strptime(end_date,'%Y/%m/%d') if end_date else datetime.datetime.now()

    start_date = datetime.datetime.strptime(start_date,'%Y/%m/%d') if start_date else end_date - datetime.timedelta(time_window)

    for log_type in log_types:

        LogModel, fields, id_field, obj_ids, objects = return_log_type_details(log_type, topic_ids)

        log_objects = LogModel.objects.filter(
            user__in=learners,
            latest_activity_timestamp__gte=start_date,
            latest_activity_timestamp__lte=end_date, **obj_ids).order_by("-latest_activity_timestamp")


        if log_type == "video":
            output_dict["content_time_spent"] += log_objects.aggregate(Sum("total_seconds_watched"))["total_seconds_watched__sum"] or 0
        elif log_type == "content":
            output_dict["content_time_spent"] += log_objects.aggregate(Sum("time_spent"))["time_spent__sum"] or 0
        elif log_type == "exercise":
            output_dict["exercise_attempts"] = AttemptLog.objects.filter(user__in=learners,
                timestamp__gte=start_date,
                timestamp__lte=end_date).count()
            if log_objects.aggregate(Avg("streak_progress"))["streak_progress__avg"] is not None:
                output_dict["exercise_mastery"] = round(log_objects.aggregate(Avg("streak_progress"))["streak_progress__avg"])
        output_logs.extend(log_objects)

    # Report total time in hours
    output_dict["content_time_spent"] = round(output_dict["content_time_spent"]/3600.0,1)
    output_logs.sort(key=lambda x: x.latest_activity_timestamp, reverse=True)
    output_dict["learner_events"] = [{
        "learner": log.user.get_name(),
        "complete": log.complete,
        "struggling": getattr(log, "struggling", None),
        "progress": getattr(log, "streak_progress", getattr(log, "progress", None)),
        "content": get_exercise_cache().get(getattr(log, "exercise_id", ""), get_content_cache().get(getattr(log, "video_id", getattr(log, "content_id", "")), {})),
        } for log in output_logs[:event_limit]]
    output_dict["total_time_logged"] = round((UserLogSummary.objects\
        .filter(user__in=learners, start_datetime__gte=start_date, start_datetime__lte=end_date)\
        .aggregate(Sum("total_seconds")).get("total_seconds__sum") or 0)/3600.0, 1)
    return JsonResponse(output_dict)
