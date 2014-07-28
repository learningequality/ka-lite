from annoying.functions import get_object_or_None
from tastypie.resources import ModelResource

from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.student_testing.models import TestLog
from securesync.models import Zone


class FacilityResource(ModelResource):
    class Meta:
        queryset = Facility.objects.all()
        resource_name = 'facility'

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering facilities by zone
        zone_id = bundle.request.GET.get('zone_id')
        if zone_id:
            facility_list = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
        else:
            facility_list = Facility.objects.all()

        return facility_list


class GroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering groups by facility
        facility_id = bundle.request.GET.get('facility_id')
        if facility_id:
            group_list = FacilityGroup.objects.filter(facility__id=facility_id)
        else:
            # TODO(dylan): this needs to be restricted to a zone?
            group_list = FacilityGroup.objects.all()

        return group_list


class TestLogResource(ModelResource):
    class Meta:
        queryset = TestLog.objects.all()
        resource_name = "test_log"

    def obj_get_list(self, bundle, *kwargs):
        # Allow filtering TestLogs by students from specific facility or group
        facility_id = bundle.request.GET.get("facility_id")
        group_id = bundle.request.GET.get("group_id")
        
        # Filter down queryset of FacilityUsers to ones that are specified by the 
        # supplied group and facility ids, if any. 
        if not facility_id or facility_id == "all":
            zone_id = bundle.request.GET.get('zone_id')
            if zone_id:
                facilities = Facility.objects.by_zone(get_object_or_None(Zone, id=zone_id))
            else:
                facilities = Facility.objects.all()
        else:
            facilities = Facility.objects.filter(id=facility_id)

        # Facility Users 
        if group_id == 'all' or not group_id: # get all students at the facility
            facility_ids = [facility.id for facility in facilities]
            facility_users = FacilityUser.objects.filter(facility__id__in=facility_ids)
        else: # get the students for the specific group
            facility_users = FacilityUser.objects.filter(group__id=group_id)

        user_ids = [u.id for u in facility_users]
        test_logs = TestLog.objects.filter(user__id__in=user_ids)

        return test_logs





