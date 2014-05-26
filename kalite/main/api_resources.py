import os
import json
from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource, Resource

from .models import VideoLog, ExerciseLog, AttemptLog

from kalite.topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes, get_exercise_data

class ExerciseLogResource(ModelResource):
    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'exerciselog'


class AttemptLogResource(ModelResource):
    class Meta:
        queryset = AttemptLog.objects.all()
        resource_name = 'attemptlog'