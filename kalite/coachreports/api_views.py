from django.utils.translation import ugettext as _
from django.db.models import Q

from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError

from kalite.main.models import ExerciseLog, VideoLog, ContentLog
from kalite.facility.models import FacilityUser
from kalite.shared.decorators.auth import require_admin
from kalite.topic_tools import get_topic_leaves

@require_admin
def learner_logs(request):

    learner_ids = request.GET.getlist("user_id")

    group_ids = request.GET.getlist("group_id")

    facility_ids = request.GET.getlist("facility_id")

    topic_ids = request.GET.getlist("topic_id", ["root"])

    learners = FacilityUser.objects.filter(Q(group__pk__in=group_ids)|Q(pk__in=learner_ids)|Q(facility__pk__in=facility_ids))

    log_types = request.GET.getlist("log_type", ["exercise", "video", "content"])

    output_logs = []

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
        obj_ids = {obj_id_field: [obj.get("id") for topic_id in topic_ids for obj in get_topic_leaves(topic_id=topic_id, leaf_type=log_type.title())]}
        output_logs.extend(LogModel.objects.filter(user__in=learners, **obj_ids).values(*fields))

    return JsonResponse(output_logs)
