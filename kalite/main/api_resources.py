from tastypie import fields
from tastypie.resources import ModelResource, Resource

from .models import VideoLog, ExerciseLog, AttemptLog

from kalite.topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes, get_exercise_data
from kalite.shared.api_auth import UserObjectsOnlyAuthorization


class ExerciseLogResource(ModelResource):
    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'exerciselog'
        filtering = {
            "exercise_id": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class AttemptLogResource(ModelResource):
    class Meta:
        queryset = AttemptLog.objects.all()
        resource_name = 'attemptlog'
        filtering = {
            "exercise_id": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()