from django.utils.translation import ugettext as _
from django.db.models import Q

from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError

from kalite.main.models import ExerciseLog, VideoLog, ContentLog
from kalite.facility.models import FacilityUser
from kalite.shared.decorators.auth import require_admin

@require_admin
def learner_logs(request):

    learner_ids = request.GET.getlist("user_id")

    group_ids = request.GET.getlist("group_id")

    facility_ids = request.GET.getlist("facility_id")

    learners = FacilityUser.objects.filter(Q(group__pk__in=group_ids)|Q(pk__in=learner_ids)|Q(facility__pk__in=facility_ids))

    log_types = request.GET.getlist("log_type", ["exercise", "video", "content"])

    output_logs = []

    for log_type in log_types:
        fields = ["user", "points", "complete", "completion_timestamp", "completion_counter"]
        if log_type == "exercise":
            LogModel = ExerciseLog
            fields.extend(["exercise_id", "attempts", "struggling", "streak_progress", "attempts_before_completion"])
        elif log_type == "video":
            LogModel = VideoLog
            fields.extend(["video_id", "total_seconds_watched"])
        elif log_type == "content":
            LogModel = ContentLog
            fields.extend(["content_id", "progress"])
        else:
            continue
        output_logs.extend(LogModel.objects.filter(user__in=learners).values(*fields))

    return JsonResponse(output_logs)
