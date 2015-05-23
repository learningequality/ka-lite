from math import ceil
import datetime

from django.utils.translation import ugettext as _
from django.db.models import Q, Sum, Avg

from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError

from kalite.main.models import ExerciseLog, VideoLog, ContentLog, AttemptLog, UserLogSummary
from kalite.facility.models import FacilityUser
from kalite.shared.decorators.auth import require_admin
from kalite.topic_tools import get_topic_leaves, get_exercise_cache, get_content_cache

@require_admin
def learner_logs(request):

    page = request.GET.get("page", 1)

    limit = request.GET.get("limit", 50)

    learner_ids = request.GET.getlist("user_id")

    group_ids = request.GET.getlist("group_id")

    facility_ids = request.GET.getlist("facility_id")

    aggregate = request.GET.get("aggregate", False)

    event_limit = request.GET.get("event_limit", 10)

    # Look back a week by default
    time_window = request.GET.get("time_window", 7)

    # Restrict filtering based on specificity. Use most specific filter (learner_ids, group_ids, facility_ids).

    if learner_ids:
        learner_filter = Q(pk__in=learner_ids)
    elif group_ids:
        learner_filter = Q(group__pk__in=group_ids)
    else:
        # Do this to ensure that we never return more than one facility's worth of anything.
        learner_filter = Q(facility__pk__in=facility_ids)

    topic_ids = request.GET.getlist("topic_id", [])

    learners = FacilityUser.objects.filter(learner_filter).order_by("last_name")

    pages = int(ceil(len(learners)/float(limit)))

    if page*limit < len(learners):

        learners = learners[(page - 1)*limit: page*limit]

    log_types = request.GET.getlist("log_type", ["exercise", "video", "content"])

    output_logs = []

    if not aggregate:

        output_objects = []
    else:
        output_dict = {
            "content_time_spent": 0,
            "exercise_attempts": 0,
            "exercise_mastery": None,
        }
    start_date = datetime.datetime.now() - datetime.timedelta(time_window)
    end_date = datetime.datetime.now()

    for log_type in log_types:
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
            continue
        id_field = obj_id_field.split("__")[0]
        if topic_ids:
            objects = [obj for topic_id in topic_ids for obj in get_topic_leaves(topic_id=topic_id, leaf_type=log_type.title())]
            obj_ids = {obj_id_field: [obj.get("id") for obj in objects]}
        else:
            obj_ids = {}
        log_objects = LogModel.objects.filter(user__in=learners, **obj_ids).values(*fields)
        if not aggregate:
            if not topic_ids:
                topic_objects = log_objects.filter(latest_activity_timestamp__gte=start_date, latest_activity_timestamp__lte=end_date)
                if topic_objects.count() == 0:
                    topic_objects = log_objects
                objects = dict([(obj[id_field], get_content_cache().get(obj[id_field], get_exercise_cache().get(obj[id_field]))) for obj in topic_objects]).values()
            output_objects.extend(objects)
        else:
            log_objects = log_objects.filter(latest_activity_timestamp__gte=start_date, latest_activity_timestamp__lte=end_date)\
                .order_by("-latest_activity_timestamp")
            if id_field == "video":
                output_dict["content_time_spent"] += log_objects.aggregate(Sum("total_seconds_watched"))["total_seconds_watched__sum"]
            elif id_field == "content":
                output_dict["content_time_spent"] += log_objects.aggregate(Sum("time_spent"))["time_spent__sum"]
            elif id_field == "exercise":
                output_dict["exercise_attempts"] = AttemptLog.objects.filter(user__in=learners,
                    latest_activity_timestamp__gte=start_date,
                    latest_activity_timestamp__lte=end_date).count()
                output_dict["exercise_mastery"] = log_objects.aggregate(Avg("streak_progress"))["streak_progress__avg"]
        output_logs.extend(log_objects)

    if aggregate:
        output_logs.sort(key=lambda x: x.latest_activity_timestamp, reverse=True)
        output_dict["learner_events"] = [{
            "learner": log.user.get_name(),
            "complete": log.complete,
            "struggling": log.struggling,
            "progress": log.streak_progress,
            "exercise": get_exercise_cache().get(log.exercise_id),
            } for log in output_logs[:event_limit]]
        output_dict["total_time_logged"] = UserLogSummary.objects\
            .filter(user__in=learners, last_activity_datetime__gte=start_date, last_activity_datetime__lte=end_date)\
            .aggregate(Sum("total_seconds")).get("total_seconds__sum") or 0
        return JsonResponse(output_dict)
    else:
        return JsonResponse({
            "logs": output_logs,
            "contents": output_objects,
            "learners": [learner for learner in learners.values("first_name", "last_name", "username", "pk")],
            "page": page,
            "pages": pages,
            "limit": limit
        })
