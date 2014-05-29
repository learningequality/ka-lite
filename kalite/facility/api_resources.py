from tastypie.authorization import Authorization
from tastypie.resources import ModelResource

from .api_authorizations import TeacherOrAdminCanReadWrite
from .models import FacilityGroup, FacilityUser


class FacilityGroupResource(ModelResource):
    class Meta:
        queryset = FacilityGroup.objects.all()
        resource_name = 'group'
        authorization = TeacherOrAdminCanReadWrite()


class FacilityUserResource(ModelResource):
    class Meta:
        queryset = FacilityUser.objects.all()
        resource_name = 'user'
        authorization = TeacherOrAdminCanReadWrite()

