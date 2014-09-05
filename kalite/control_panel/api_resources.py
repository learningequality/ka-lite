from annoying.functions import get_object_or_None
from tastypie.exceptions import NotFound, BadRequest
from tastypie.resources import Resource, ModelResource
from tastypie.serializers import Serializer

from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.main.models import AttemptLog
from kalite.shared.api_auth import ObjectAdminAuthorization
from kalite.student_testing.models import TestLog
from securesync.models import Zone

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

    def _get_facility_user_list(self, bundle):
        """Return a list of facility users specified by the zone id(s), facility_id, or group_id"""
        zone_id = bundle.request.GET.get('zone_id')
        zone_ids = bundle.request.GET.get('zone_ids')
        facility_id = bundle.request.GET.get('facility_id')
        group_id = bundle.request.GET.get('group_id')

        # They must have a zone_id, and may have a facility_id and group_id.
        # Try to filter from most specific, to least 
        facility_user_list = []
        if group_id:
            facility_user_list = FacilityUser.objects.filter(group__id=group_id)
        elif facility_id:
            facility_user_list = FacilityUser.objects.filter(facility__id=facility_id)
        elif zone_id:
            facility_user_list = FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        elif zone_ids:
            # Assume 'all' selected for zone, and a list of zone ids has been passed
            zone_ids = zone_ids.split(",")
            facility_user_list = []
            for zone_id in zone_ids:
                facility_user_list += FacilityUser.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        else:
            raise BadRequest("Invalid request.")

        if not facility_user_list:
            raise NotFound("Student not found.")

        return facility_user_list

class FacilityUserResource(ParentFacilityUserResource):

    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'facility_user'
        authorization = ObjectAdminAuthorization()
        excludes = ['password', 'signature', 'deleted', 'signed_version', 'counter']
        serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        facility_user_list = self._get_facility_user_list(bundle)
        # call super to trigger auth
        return super(FacilityUserResource, self).authorized_read_list(facility_user_list, bundle)


class TestLogResource(ParentFacilityUserResource):

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'test_log'
        authorization = ObjectAdminAuthorization()
        excludes = []
        serializer = Serializer()
        # serializer = CSVSerializer()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering based on zone, facility, group
        facility_user_list = self._get_facility_user_list(bundle)
        facility_user_ids = [facility_user.id for facility_user in facility_user_list]
        test_logs = TestLog.objects.filter(user__id__in=facility_user_ids)
        return super(TestLogResource, self).authorized_read_list(test_logs, bundle)


class AttemptLogResource(ParentFacilityUserResource):

    class Meta:
        queryset = AttemptLog.objects.all()
        resource_name = 'attempt_log'
        authorization = ObjectAdminAuthorization()
        excludes = []
        # serializer = CSVSerializer()
        serializer = Serializer()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering based on zone, facility, group
        facility_user_list = self._get_facility_user_list(bundle)
        facility_user_ids = [facility_user.id for facility_user in facility_user_list]
        attempt_logs = AttemptLog.objects.filter(user__id__in=facility_user_ids)
        return super(AttemptLogResource, self).authorized_read_list(attempt_logs, bundle)


