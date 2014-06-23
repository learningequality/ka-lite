import glob
import json
import os

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

from django.conf import settings

logging = settings.LOG

testscache = {}


class Test():
    def __init__(self, **kwargs):
        test_id = kwargs.get('test_id')
        self.title = kwargs.get('title')
        self.ids = json.dumps(kwargs.get('ids'))
        self.playlist_ids = json.dumps(kwargs.get('playlist_ids'))
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')
        self.test_id = test_id
        self.test_url = reverse('test', args=[test_id])
        self.set_exam_mode()

    def set_exam_mode(self):
        # check if exam mode is active on specific exam
        is_exam_mode = False
        exam_mode_setting = get_exam_mode_on()
        if exam_mode_setting and exam_mode_setting == self.test_id:
            is_exam_mode = True
        self.is_exam_mode = is_exam_mode


class TestLogResource(ModelResource):

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "test": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserObjectsOnlyAuthorization()


class TestResource(Resource):

    title = fields.CharField(attribute='title')
    ids = fields.CharField(attribute='ids')
    playlist_ids = fields.CharField(attribute='playlist_ids')
    seed = fields.IntegerField(attribute='seed')
    repeats = fields.IntegerField(attribute='repeats')
    test_id = fields.CharField(attribute='test_id')
    test_url = fields.CharField(attribute='test_url')
    is_exam_mode = fields.BooleanField(attribute='is_exam_mode')

    class Meta:
        resource_name = 'test'
        object_class = Test

    def _refresh_tests_cache(self):
        for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):
            with open(testfile) as f:
                data = json.load(f)
                # Coerce each test dict into a Test object
                # also add in the group IDs that are assigned to view this test
                test_id = os.path.splitext(os.path.basename(f.name))[0]
                data["test_id"] = test_id
                testscache[test_id] = (Test(**data))

    def _read_test(self, test_id, force=False):
        if not testscache or force:
            self._refresh_tests_cache()
        return testscache.get(test_id, None)

    def _read_tests(self, test_id=None, force=False):
        if not testscache or force:
            self._refresh_tests_cache()
        return sorted(testscache.values(), key=lambda test: test.title)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<test_id>[\w\d_.-]+)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"),
        ]

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if getattr(bundle_or_obj, 'obj', None):
            kwargs['pk'] = bundle_or_obj.obj.test_id
        else:
            kwargs['pk'] = bundle_or_obj.test_id
        return kwargs

    def get_object_list(self, request, force=False):
        """
        Get the list of tests based from a request.
        """
        if not request.is_admin:
            return [] 
        return self._read_tests(force=force)

    def obj_get_list(self, bundle, **kwargs):
        # logging.warn('==> API get_list %s -- %s' % (bundle.request.user, bundle.request.is_teacher,))
        if not bundle.request.is_admin:
            raise Unauthorized(_("You are not authorized to view this page."))
        force = bundle.request.GET.get('force', False)
        return self.get_object_list(bundle.request, force=force)

    def obj_get(self, bundle, **kwargs):
        # logging.warn('==> API get %s -- %s' % (bundle.request.user, bundle.request.is_teacher,))
        test_id = kwargs.get("test_id", None)
        test = self._read_test(test_id)
        if test:
            return test
        else:
            raise NotFound('Test with test_id %s not found' % test_id)

    def obj_create(self, request):
        # logging.warn('==> API create %s -- %s' % (request.user, request.is_teacher,))
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_update(self, bundle, **kwargs):
        """
        Receives a `test_id` and sets it as the Settings.EXAM_MODE_ON value.
        If `test_id` is the same on the Settings, means it's a toggle so we disable it.
        Validates if user is an admin.
        """
        # logging.warn('==> API update %s -- %s' % (bundle.request.user, bundle.request.is_teacher,))
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot set this test into exam mode."))
        try:
            test_id = kwargs['test_id']
            obj, created = Settings.objects.get_or_create(name=SETTINGS_KEY_EXAM_MODE)
            if obj.value == test_id:
                obj.value = ''
            else:
                obj.value = test_id
            obj.save()
            testscache[test_id].set_exam_mode()
            return bundle
        except Exception as e:
            logging.error("==> TestResource exception: %s" % e)
            pass
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete_list(self, request):
        # logging.warn('==> API delete_list %s' % request.user)
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete(self, request):
        # logging.warn('==> API delete %s' % request.user)
        raise NotImplemented("Operation not implemented yet for tests.")

    def rollback(self, request):
        # logging.warn('==> API rollback %s' % request.user)
        raise NotImplemented("Operation not implemented yet for tests.")
