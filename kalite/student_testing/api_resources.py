import glob
import os
import json
from tastypie import fields
from tastypie.resources import ModelResource, Resource

from .models import TestLog
from kalite.shared.api_auth import UserObjectsOnlyAuthorization


class Test:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title')
        self.ids = kwargs.get('ids')
        self.playlist_ids = kwargs.get('playlist_ids')
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')

class TestLogResource(ModelResource):
    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "title": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()

class TestResource(ModelResource):
    class Meta:
        resource_name = 'test'
        object_class = Test

    def read_tests(self):
        raw_tests = []
        for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json")
            with open(testfile) as f:
                raw_tests.append(json.load(f))

        # Coerce each test dict into a Test object
        # also add in the group IDs that are assigned to view this test
        tests = []
        for test_dict in raw_tests:
            test = Test(**test_dict)
            tests.append(test)

        return tests

    def get_object_list(self, request):
        '''Get the list of tests based from a request'''
        return self.read_tests()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        tests = self.read_tests()
        title = kwargs['title']
        for test in tests:
            if str(test.title) == title:
                return test
        else:
            raise NotFound('Test with title %s not found' % title)

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