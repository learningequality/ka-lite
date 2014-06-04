import glob
import json

from django.conf.urls import url
from django.core.urlresolvers import reverse

from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource, Resource

from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource

from .models import TestLog
from .settings import STUDENT_TESTING_DATA_PATH


# TODO(cpauya): 1. Save exam mode setting by teacher from front-end.  Only one exam at a time can be enabled at Setting.EXAM_MODE_ON.
# TODO(cpauya): 2. Redirect student to exam page if exam mode is on.


class Test():
    def __init__(self, **kwargs):
        title = kwargs.get('title')
        self.title = title
        self.ids = json.dumps(kwargs.get('ids'))
        self.playlist_ids = json.dumps(kwargs.get('playlist_ids'))
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')
        self.test_url = reverse('test', args=[title])


class TestLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "title": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class TestResource(Resource):

    title = fields.CharField(attribute='title')
    ids = fields.CharField(attribute='ids')
    playlist_ids = fields.CharField(attribute='playlist_ids')
    seed = fields.IntegerField(attribute='seed')
    repeats = fields.IntegerField(attribute='repeats')
    test_url = fields.CharField(attribute='test_url')

    class Meta:
        resource_name = 'test'
        object_class = Test

    def _read_tests(self, title=None):
        raw_tests = []
        for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):
            with open(testfile) as f:
                raw_tests.append(json.load(f))

        # Coerce each test dict into a Test object
        # also add in the group IDs that are assigned to view this test
        tests = []
        for test_dict in raw_tests:
            test = Test(**test_dict)
            if title and test.title == title:
                return test
            tests.append(test)
        if title:
            return None

        # MUST: sort the tests based on title for user's sanity
        tests = sorted(tests, key=lambda test: test.title)
        return tests

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<title>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.title
        else:
            kwargs['pk'] = bundle_or_obj.title
        return kwargs

    def get_object_list(self, request):
        """
        Get the list of tests based from a request.
        """
        return self._read_tests()

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)

    def obj_get(self, bundle, **kwargs):
        title = kwargs.get("pk", None)
        test = self._read_tests(title)
        if test:
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
