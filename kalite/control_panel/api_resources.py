from annoying.functions import get_object_or_None
from tastypie.resources import ModelResource

from kalite.facility.models import Facility, FacilityGroup
from kalite.shared.api_auth import ZoneAdminAuthorization
from securesync.models import Zone


class FacilityResource(ModelResource):
    class Meta:
        queryset = Facility.objects.all()
        resource_name = 'facility'
        filtering = {
            "facility_id": ('exact',),
            "zone_id": ('exact',),
        }
        authorization = ZoneAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering facilities by zone
        super(FacilityResource, self).obj_get_list(bundle, **kwargs)
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
        authorization = ZoneAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Allow filtering groups by facility
        super(GroupResource, self).obj_get_list(bundle, **kwargs)
        facility_id = bundle.request.GET.get('facility_id')
        if facility_id:
            group_list = FacilityGroup.objects.filter(facility__id=facility_id)
        else:
            # TODO(dylan): this needs to be restricted to a zone?
            group_list = FacilityGroup.objects.all()

        return group_list
