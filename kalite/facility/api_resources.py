from tastypie.resources import ModelResource

from .api_authorizations import FacilityUserCanWriteAuthorization
from .models import FacilityGroup


class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        authorization = FacilityUserCanWriteAuthorization()
