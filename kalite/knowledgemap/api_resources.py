from tastypie import fields
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource

from kalite.shared.decorators import get_user_from_request

from kalite.facility.api_resources import FacilityUserResource
from kalite.coachreports.api_resources import ExerciseSummaryResource
from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.main.models import ExerciseLog

class KnowledgeMapExerciseResource(ExerciseSummaryResource):

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'KnowledgeMapExerciselog'
        filtering = {
            "exercise_id": ['exact'],
            "user": ['exact'],
            "completion_timestamp": ['gte', 'lte']
        }

        excludes = ['attempts_before_completion', 
            'complete', 'counter', 'attempts', 'language', 'signed_version',
            'points', 'completion_counter',
            'mastered', 'struggling', 'deleted'
            ]
        authorization = UserObjectsOnlyAuthorization()

    # def get_object_list(self, request):
    #     # self.permission_check(request)
    #     # user = get_user_from_request(request=request)
    #     #     if request.GET.get("user_id") == user.id:
    #     #         pass
    #     #     else:
    #     #         raise Unauthorized(_("You requested information for a user that you are not authorized to view."))
    #     # user = request.session["facility_user"]
    #     # if user:
    #     # user = get_user_from_request(request=request)
    #     # user_id = user.id
    #     user_id = request.GET.get('user_id')
    #     # else:
    #     #     user__exact="aa10aa46ae3d5f8e981148529301d9fd"

    #     return super(ExerciseSummaryResource, self).get_object_list(request).filter(
    #         completion_timestamp__gte='2014-11-25', 
    #         completion_timestamp__lte='2014-12-22',
    #         user__exact=user_id)
    #         # user="19bf8439722252ff854c2b9126f86e8f")
            # Guan Wong:
            # user__exact="19bf8439722252ff854c2b9126f86e8f")
            # Sofia Brown:
            # user__exact="5596a405a92154b2a25e753127963a43")
            # Guan Brown:
            # user__exact="aa10aa46ae3d5f8e981148529301d9fd")
            # Zenab Mench:
            # user__exact="bf5235e6d7af581da99be187bddcb2b7")

    # def obj_get_list(self, bundle, **kwargs):
    #     # self.permission_check(bundle.request)
    #     exercise_logs = self.get_object_list(bundle.request)
    #     return exercise_logs