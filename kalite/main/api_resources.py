import os
import json
from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource, Resource
from tastypie.authorization import Authorization

from django.conf import settings;

from .models import VideoLog, ExerciseLog, AttemptLog

from kalite.topic_tools import get_flat_topic_tree, get_node_cache, get_neighbor_nodes, get_exercise_data

class UserObjectsOnlyAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``
        if (settings.CENTRAL_SERVER and bundle.request.user.is_authenticated()) or getattr(bundle.request, "is_admin", False):
            return object_list.filter()
        else:
            user = bundle.request.session.get("facility_user", None)
            if user != bundle.request.GET.get("user", None):
                raise Unauthorized("Sorry, that information is restricted.")
            else:
                return object_list.filter(user=user)

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        if (settings.CENTRAL_SERVER and bundle.request.user.is_authenticated()) or getattr(bundle.request, "is_admin", False):
            return True
        else:
            return bundle.obj.user == bundle.request.session.get("facility_user", None)

    def create_list(self, object_list, bundle):
        # Assuming they're auto-assigned to ``user``.
        return object_list

    def create_detail(self, object_list, bundle):
        if (settings.CENTRAL_SERVER and bundle.request.user.is_authenticated()) or getattr(bundle.request, "is_admin", False):
            return True
        else:
            return bundle.obj.user == bundle.request.session.get("facility_user", None)

    def update_list(self, object_list, bundle):
        allowed = []

        # Since they may not all be saved, iterate over them.
        for obj in object_list:
            if (settings.CENTRAL_SERVER and bundle.request.user.is_authenticated()) or getattr(bundle.request, "is_admin", False) or bundle.obj.user == bundle.request.session.get("facility_user", None):
                allowed.append(obj)

        return allowed

    def update_detail(self, object_list, bundle):
        if (settings.CENTRAL_SERVER and bundle.request.user.is_authenticated()) or getattr(bundle.request, "is_admin", False):
            return True
        else:
            return bundle.obj.user == bundle.request.session.get("facility_user", None)

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")



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