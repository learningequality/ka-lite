from tastypie import fields
from tastypie.resources import ModelResource, Resource

from .models import TestLog
from kalite.shared.api_auth import UserObjectsOnlyAuthorization


class TestLogResource(ModelResource):
    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "title": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()