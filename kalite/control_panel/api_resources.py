from annoying.functions import get_object_or_None
from tastypie.resources import ModelResource

from kalite.facility.models import Facility, FacilityGroup
from kalite.shared.api_auth import ObjectAdminAuthorization
from securesync.models import Zone


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

        kwargs.update({"object_list": facility_list})

        # call super to trigger auth
        super(FacilityResource, self).obj_get_list(bundle, **kwargs)
        
        return facility_list

class GroupResource(ModelResource):
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

        kwargs.update({"object_list": group_list})

        # call super to trigger auth
        super(GroupResource, self).obj_get_list(bundle, **kwargs)

        return group_list
