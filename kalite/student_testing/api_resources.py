import glob
import json
import logging

from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource, Resource

from fle_utils.config.models import Settings

from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource

from .models import TestLog
from .settings import SETTINGS_KEY_EXAM_MODE, STUDENT_TESTING_DATA_PATH
from .utils import get_exam_mode_on


class Test():
    def __init__(self, **kwargs):
        title = kwargs.get('title')
        self.title = title
        self.ids = json.dumps(kwargs.get('ids'))
        self.playlist_ids = json.dumps(kwargs.get('playlist_ids'))
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')
        self.test_url = reverse('test', args=[title])

        # check if exam mode is active on specific exam
        is_exam_mode = False
        exam_mode_setting = get_exam_mode_on()
        if exam_mode_setting and exam_mode_setting == title:
            is_exam_mode = True
        self.is_exam_mode = is_exam_mode


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
    is_exam_mode = fields.BooleanField(attribute='is_exam_mode')

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
        if not request.is_admin:
            return []
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
        """
        Receives an exam_title and sets it as the Settings.EXAM_MODE_ON value.
        If exam_title are the same on the Settings, means it's a toggle so we disable it.
        Validates if user is an admin.
        """
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot set this test into exam mode."))
        try:
            exam_title = kwargs['pk']
            obj, created = Settings.objects.get_or_create(name=SETTINGS_KEY_EXAM_MODE)
            if obj.value == exam_title:
                obj.value = ''
            else:
                obj.value = exam_title
            obj.save()
            return bundle
        except Exception as e:
            logging.error("==> TestResource exception: %s" % e)
            pass
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")
