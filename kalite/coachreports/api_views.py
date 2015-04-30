from django.utils.translation import ugettext as _
from django.db.models import Q

from fle_utils.internet.classes import JsonResponse, JsonResponseMessage, JsonResponseMessageError

from kalite.main.models import ExerciseLog, VideoLog, ContentLog
from kalite.facility.models import FacilityUser
from kalite.shared.decorators.auth import require_admin

@require_admin
def learner_logs(request):

    learner_ids = request.GET.getlist("user_id")

    group_ids = request.GET.getlist("group_ids")

    facility_ids = request.GET.getlist("facility_ids")

    learners = FacilityUser.objects.filter(Q(group__pk__in=group_ids)|Q(pk__in=learner_ids)|Q(facility__pk__in=facility_ids))



        
