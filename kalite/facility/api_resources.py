from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from .api_authorizations import FacilityUserCanWriteAuthorization
from .models import FacilityGroup, FacilityUser


class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        # authorization = FacilityUserCanWriteAuthorization()
        authorization = Authorization()


class FacilityUserResource(ModelResource):
    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'user'
        # authorization = FacilityUserCanWriteAuthorization()
        authorization = Authorization()

