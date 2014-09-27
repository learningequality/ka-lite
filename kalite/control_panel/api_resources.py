from annoying.functions import get_object_or_None
from datetime import datetime
from django.http import HttpResponse
from tastypie import fields
from tastypie.exceptions import NotFound, BadRequest
from tastypie.resources import Resource, ModelResource

from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.main.models import AttemptLog, ExerciseLog
from kalite.shared.api_auth import ObjectAdminAuthorization
from kalite.student_testing.models import TestLog
from securesync.models import Zone, Device, SyncSession

from .api_serializers import CSVSerializer


class FacilityResource(ModelResource):
    class Meta:
        queryset = Facility.objects.all()
        resource_name = 'facility'
        authorization = ObjectAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering facilities by zone
        zone_id = bundle.request.GET.get('zone_id')
        if zone_id:
            facility_list = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        else:
            facility_list = Facility.objects.all()

        # call super to trigger auth
        return super(FacilityResource, self).authorized_read_list(facility_list, bundle)
        

class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        authorization = ObjectAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering groups by facility
        facility_id = bundle.request.GET.get('facility_id')
        if facility_id:
            group_list = FacilityGroup.objects.filter(facility__id=facility_id)
        else:
            group_list = FacilityGroup.objects.all()

        # call super to trigger auth
        return super(FacilityGroupResource, self).authorized_read_list(group_list, bundle)


class ParentFacilityUserResource(ModelResource):
    """A class with helper methods for getting facility users for data export requests"""

    def _get_facility_users(self, bundle):
        """Return a dict mapping facility_user_ids to facility user objs, filtered by the zone id(s), facility_id, or group_id"""
        zone_id = bundle.request.GET.get('zone_id')
        zone_ids = bundle.request.GET.get('zone_ids')
        facility_id = bundle.request.GET.get('facility_id')
        group_id = bundle.request.GET.get('group_id')

        # They must have a zone_id, and may have a facility_id and group_id.
        # Try to filter from most specific, to least 
        facility_user_objects = []
        if group_id:
            facility_user_objects = FacilityUser.objects.filter(group__id=group_id)
        elif facility_id:
            facility_user_objects = FacilityUser.objects.filter(facility__id=facility_id)
        elif zone_id:
            facility_user_objects = FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        elif zone_ids:
            # Assume 'all' selected for zone, and a list of zone ids has been passed
            zone_ids = zone_ids.split(",")
            facility_user_objects = []
            for zone_id in zone_ids:
                facility_user_objects += FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        # TODO(dylanjbarth) errors commented out so we can pass a blank CSV if not found.
        # in future, should handle these more gracefully, with a redirect, an AJAX warning,
        # and reset the fields. see: https://gist.github.com/1116962/58b7db0364de837ce229cdd8ef524bc9ff6da19f
        # else:
        #     raise BadRequest("Invalid request.")

        # if not facility_user_objects:
        #     raise NotFound("Student not found.")
        facility_user_dict = {}
        for user in facility_user_objects:
            facility_user_dict[user.id] = user
        return facility_user_dict

    def create_response(self, request, data, response_class=HttpResponse, **response_kwargs):
        response = super(ParentFacilityUserResource, self).create_response(request, data, response_class=response_class, **response_kwargs)
        # add a suggested download filename if we're replying with a CSV file
        if response["Content-Type"].startswith("text/csv"):
            params = ["%s-%s" % (k,str(v)[0:8]) for (k,v) in request.GET.items() if v and k not in ["format", "limit"]]
            response["Content-Disposition"] = "filename=%s__%s__exported_at-%s.csv" % (request.path.strip("/").split("/")[-1], "__".join(params), datetime.now().strftime("%Y%m%d_%H%M%S"))
        return response

class FacilityUserResource(ParentFacilityUserResource):

    _facility_users = None

    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'facility_user_csv'
        authorization = ObjectAdminAuthorization()
        excludes = ['password', 'signature', 'deleted', 'signed_version', 'counter', 'notes']
        serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        self._facility_users = self._get_facility_users(bundle)
        return super(FacilityUserResource, self).authorized_read_list(self._facility_users.values(), bundle)

    def alter_list_data_to_serialize(self, request, to_be_serialized):
        """Add facility name, and facility ID to responses"""
        for bundle in to_be_serialized["objects"]:
            user = self._facility_users.get(bundle.data["id"])
            bundle.data["facility_name"] = user.facility.name
            bundle.data["facility_id"] = user.facility.id

        return to_be_serialized


class TestLogResource(ParentFacilityUserResource):

    _facility_users = None

    user = fields.ForeignKey(FacilityUserResource, 'user', full=True)

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'test_log_csv'
        authorization = ObjectAdminAuthorization()
        excludes = ['user', 'counter', 'signature', 'deleted', 'signed_version']
        serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        self._facility_users = self._get_facility_users(bundle)
        test_logs = TestLog.objects.filter(user__id__in=self._facility_users.keys())
        # if not test_logs:
        #     raise NotFound("No test logs found.")
        return super(TestLogResource, self).authorized_read_list(test_logs, bundle)

    def alter_list_data_to_serialize(self, request, to_be_serialized):
        """Add username, facility name, and facility ID to responses"""
        for bundle in to_be_serialized["objects"]:
            user_id = bundle.data["user"].data["id"]
            user = self._facility_users.get(user_id)
            bundle.data["username"] = user.username
            bundle.data["facility_name"] = user.facility.name
            bundle.data["facility_id"] = user.facility.id
            bundle.data.pop("user")

        return to_be_serialized


class AttemptLogResource(ParentFacilityUserResource):

    _facility_users = None

    user = fields.ForeignKey(FacilityUserResource, 'user', full=True)

    class Meta:
        queryset = AttemptLog.objects.all()
        resource_name = 'attempt_log_csv'
        authorization = ObjectAdminAuthorization()
        excludes = ['user', 'signed_version', 'language', 'deleted', 'response_log', 'signature', 'version', 'counter']
        serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        self._facility_users = self._get_facility_users(bundle)
        attempt_logs = AttemptLog.objects.filter(user__id__in=self._facility_users.keys())
        # if not attempt_logs:
        #     raise NotFound("No attempt logs found.")
        return super(AttemptLogResource, self).authorized_read_list(attempt_logs, bundle)

    def alter_list_data_to_serialize(self, request, to_be_serialized):
        """Add username, facility name, and facility ID to responses"""
        for bundle in to_be_serialized["objects"]:
            user_id = bundle.data["user"].data["id"]
            user = self._facility_users.get(user_id)
            bundle.data["username"] = user.username
            bundle.data["facility_name"] = user.facility.name
            bundle.data["facility_id"] = user.facility.id
            bundle.data.pop("user")

        return to_be_serialized


class ExerciseLogResource(ParentFacilityUserResource):

    _facility_users = None

    user = fields.ForeignKey(FacilityUserResource, 'user', full=True)

    class Meta:
        queryset = ExerciseLog.objects.all()
        resource_name = 'exercise_log_csv'
        authorization = ObjectAdminAuthorization()
        excludes = ['signed_version', 'counter', 'signature']
        serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        self._facility_users = self._get_facility_users(bundle)
        exercise_logs = ExerciseLog.objects.filter(user__id__in=self._facility_users.keys())
        # if not exercise_logs:
        #     raise NotFound("No exercise logs found.")
        return super(ExerciseLogResource, self).authorized_read_list(exercise_logs, bundle)

    def alter_list_data_to_serialize(self, request, to_be_serialized):
        """Add username, facility name, and facility ID to responses"""
        for bundle in to_be_serialized["objects"]:
            user_id = bundle.data["user"].data["id"]
            user = self._facility_users.get(user_id)
            bundle.data["username"] = user.username
            bundle.data["facility_name"] = user.facility.name
            bundle.data["facility_id"] = user.facility.id
            bundle.data.pop("user")

        return to_be_serialized


class DeviceLogResource(ParentFacilityUserResource):

    class Meta:
        queryset = Device.objects.all()
        resource_name = 'device_log_csv'
        authorization = ObjectAdminAuthorization()
        excludes = ['signed_version', 'public_key', 'counter', 'signature']
        serializer = CSVSerializer()

    def _get_device_logs(self, bundle):
        # requires at least one zone_id, which we pass as a list to zone_ids
        zone_ids = bundle.request.GET.get("zone_id") or bundle.request.GET.get("zone_ids")
        return Device.objects.by_zones(zone_ids.split(","))

    def obj_get_list(self, bundle, **kwargs):
        device_logs = self._get_device_logs(bundle)
        return super(DeviceLogResource, self).authorized_read_list(device_logs, bundle)

    def alter_list_data_to_serialize(self, request, to_be_serialized):
        """Add number of syncs and last sync to response"""
        for bundle in to_be_serialized["objects"]:
            all_sessions = SyncSession.objects.filter(client_device__id=bundle.data.get("id"))
            last_sync = "Never" if not all_sessions else all_sessions.order_by("-timestamp")[0].timestamp
            bundle.data["last_sync"] = last_sync
            bundle.data["total_sync_sessions"] = len(all_sessions)

        return to_be_serialized

