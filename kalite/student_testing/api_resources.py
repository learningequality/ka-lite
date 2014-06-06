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
        self.test_id = kwargs.get('test_id')

class TestLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "test_id": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()

class TestResource(Resource):

    title = fields.CharField(attribute='title')
    ids = fields.CharField(attribute='ids')
    seed = fields.IntegerField(attribute='seed')
    repeats = fields.IntegerField(attribute='repeats')
    test_id = fields.CharField(attribute='test_id')

    class Meta:
        resource_name = 'test'
        object_class = Test

    def _read_tests(self, test_id=None, force=False):
        if not testscache or force:
            for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):
                with open(testfile) as f:
                    data = json.load(f)
                    data["test_id"] = os.path.splitext(os.path.basename(f.name))[0]
                    testscache.append(Test(**data))

        # Coerce each test dict into a Test object
        # also add in the group IDs that are assigned to view this test
        if test_id:
            for test in testscache:
                if test_id and test.test_id == test_id:
                    return test
            return None

        return testscache

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<test_id>[\w\d_.-]+)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.test_id
        else:
            kwargs['pk'] = bundle_or_obj.test_id

        return kwargs

    def get_object_list(self, request):
        '''Get the list of tests based from a request'''
        return self._read_tests()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        test_id = kwargs.get("test_id", None)
        test = self._read_tests(test_id)
        if test:
            return test
        else:
            raise NotFound('Test with test_id %s not found' % test_id)

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
