import glob
import os
import json
from django.db import models
from django.conf.urls.defaults import url
from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource, Resource

from .models import TestLog
from .settings import STUDENT_TESTING_DATA_PATH
from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource

testscache = []

class Test():
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.ids = json.dumps(kwargs.get('ids'))
        self.playlist_ids = kwargs.get('playlist_ids')
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')
        self.pk = kwargs.get('pk')

class TestLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "pk": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()

class TestResource(Resource):

    title = fields.CharField(attribute='title')
    ids = fields.CharField(attribute='ids')
    seed = fields.IntegerField(attribute='seed')
    repeats = fields.IntegerField(attribute='repeats')
    pk = fields.CharField(attribute='pk')

    class Meta:
        resource_name = 'test'
        object_class = Test

    def _read_tests(self, pk=None, force=False):
        if not testscache or force:
            for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):
                with open(testfile) as f:
                    data = json.load(f)
                    data["pk"] = os.path.splitext(os.path.basename(f.name))[0]
                    testscache.append(Test(**data))

        # Coerce each test dict into a Test object
        # also add in the group IDs that are assigned to view this test
        if pk:
            for test in testscache:
                if pk and test.pk == pk:
                    return test
            return None

        return testscache

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def get_object_list(self, request):
        '''Get the list of tests based from a request'''
        return self._read_tests()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        pk = kwargs.get("pk", None)
        test = self._read_tests(pk)
        if test:
            return test
        else:
            raise NotFound('Test with pk %s not found' % pk)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_update(self, bundle, **kwargs):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")
