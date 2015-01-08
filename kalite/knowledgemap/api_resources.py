from tastypie import fields
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource

from kalite.shared.decorators import get_user_from_request

from kalite.facility.api_resources import FacilityUserResource
from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.main.models import ExerciseLog

class ExerciseSummaryResource(ModelResource):
    user = fields.ForeignKey(FacilityUserResource, 'user')

    def obj_create(self, bundle, **kwargs):
        is_admin = getattr(bundle.request, "is_admin", False)
        user = getattr(bundle.request, "user", None)
        if is_admin:
            if user and getattr(user, 'is_superuser', False):
                return None
        return super(ExerciseLogResource, self).obj_create(bundle, **kwargs)

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