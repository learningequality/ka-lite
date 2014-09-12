import os

from random import randint

from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from tastypie import fields
from tastypie.exceptions import NotFound, Unauthorized
from tastypie.resources import ModelResource, Resource

from fle_utils.config.models import Settings
from fle_utils.internet import api_handle_error_with_json

from kalite.shared.api_auth import UserObjectsOnlyAuthorization
from kalite.facility.api_resources import FacilityUserResource
from kalite.facility.models import Facility
from kalite.playlist import UNITS

from .models import Test, TestLog
from .settings import SETTINGS_KEY_EXAM_MODE
from .utils import get_exam_mode_on, set_exam_mode_on, get_current_unit_settings_value, set_current_unit_settings_value

from django.conf import settings

logging = settings.LOG

class UserTestObjectsOnlyAuthorization(UserObjectsOnlyAuthorization):

    def check_test(self, bundle):

        test_id = bundle.obj.test or bundle.request.GET.get("test", "")

        if (not self._user_is_admin(bundle)) and test_id != get_exam_mode_on():
            raise Unauthorized("Sorry, the test is not currently active.")

    def create_list(self, object_list, bundle):

        self.check_test(bundle)

        return super(UserTestObjectsOnlyAuthorization, self).create_list(object_list, bundle)

    def create_detail(self, object_list, bundle):

        self.check_test(bundle)

        return super(UserTestObjectsOnlyAuthorization, self).create_detail(object_list, bundle)

    def update_list(self, object_list, bundle):

        self.check_test(bundle)

        return super(UserTestObjectsOnlyAuthorization, self).update_list(object_list, bundle)

    def update_detail(self, object_list, bundle):

        self.check_test(bundle)

        return super(UserTestObjectsOnlyAuthorization, self).update_detail(object_list, bundle)

class TestLogResource(ModelResource):

    def wrap_view(self, view):
        """
        Wraps views to return custom error codes instead of generic 500's
        """
        def wrapper(request, *args, **kwargs):
            try:
                callback = getattr(self, view)
                response = callback(request, *args, **kwargs)

                # response is a HttpResponse object, so follow Django's instructions
                # to change it to your needs before you return it.
                # https://docs.djangoproject.com/en/dev/ref/request-response/
                return response
            except Exception as e:
                # Rather than re-raising, we're going to things similar to
                # what Django does. The difference is returning a serialized
                # error message.
                return self._handle_500(request, e)

        return wrapper

    user = fields.ForeignKey(FacilityUserResource, 'user')

    class Meta:
        queryset = TestLog.objects.all()
        resource_name = 'testlog'
        filtering = {
            "test": ('exact', ),
            "user": ('exact', ),
        }
        authorization = UserTestObjectsOnlyAuthorization()


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

    def _read_test(self, test_id, force=False):
        testscache = Test.all(force=force)
        return testscache.get(test_id, None)

    def _read_tests(self, test_id=None, force=False):
        testscache = Test.all(force=force)
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
        if not bundle.request.is_admin:
            raise Unauthorized(_("You are not authorized to view this page."))
        force = bundle.request.GET.get('force', False)
        return self.get_object_list(bundle.request, force=force)

    def obj_get(self, bundle, **kwargs):
        test_id = kwargs.get("test_id", None)
        test = self._read_test(test_id)
        if test:
            return test
        else:
            raise NotFound('Test with test_id %s not found' % test_id)

    def obj_create(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_update(self, bundle, **kwargs):
        """
        Receives a `test_id` and sets it as the Settings.EXAM_MODE_ON value.
        If `test_id` is the same on the Settings, means it's a toggle so we disable it.
        Validates if user is an admin.
        """
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot set this test into exam mode."))
        try:
            test_id = kwargs['test_id']
            testscache = Test.all()
            set_exam_mode_on(testscache[test_id])
            return bundle
        except Exception as e:
            logging.error("TestResource exception: %s" % e)
            pass
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete_list(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def obj_delete(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")

    def rollback(self, request):
        raise NotImplemented("Operation not implemented yet for tests.")


# ==========================
# TastyPie classes
# ==========================

class CurrentUnit():
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '<id>')
        self.facility_id = kwargs.get('facility_id', '')
        self.facility_name = kwargs.get('facility_name', '<facility_name>')
        self.facility_url = kwargs.get('facility_url', '<facility_url>')
        self.unit_list = kwargs.get('unit_list', UNITS)
        self.current_unit = kwargs.get('current_unit', self._get_current_unit())
        self.max_unit = max(UNITS)
        self.min_unit = min(UNITS)

    def __unicode__(self):
        return self.facility_name

    def _get_current_unit(self):
        # get active unit for the Facility from Settings
        current_unit = 1
        if self.facility_id:
            current_unit = get_current_unit_settings_value(self.facility_id)
        return current_unit


class CurrentUnitResource(Resource):

    id = fields.CharField(attribute='id')
    facility_id = fields.CharField(attribute='facility_id')
    facility_name = fields.CharField(attribute='facility_name')
    facility_url = fields.CharField(attribute='facility_url')
    current_unit = fields.IntegerField(attribute='current_unit', default=1)
    min_unit = fields.IntegerField(attribute='min_unit', default=1)
    max_unit = fields.IntegerField(attribute='max_unit', default=8)
    unit_list = fields.ListField(attribute='unit_list')

    class Meta:
        resource_name = 'current_unit'
        object_class = CurrentUnit

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, CurrentUnit):
            kwargs['pk'] = bundle_or_obj.id
        else:
            kwargs['pk'] = bundle_or_obj.obj.id
        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        """
        Get the list of facilities based from a request.
        """
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot view these objects."))

        objects = []
        for facility in Facility.objects.order_by('name'):
            url = reverse('facility_management', args=[None, facility.id])
            data = {
                'id': facility.id,
                'facility_id': facility.id,
                'facility_name': facility.name,
                'facility_url': url
            }
            o = CurrentUnit(**data)
            objects.append(o)
        return objects


    def get_object_list(self, request, force=False):
        raise NotImplemented(_("Operation not implemented."))

    def obj_create(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def obj_update(self, bundle, **kwargs):
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot update this object."))
        try:
            facility_id = bundle.data.get('facility_id', '')
            current_unit = int(bundle.data.get('current_unit', '0'))
            assert current_unit in UNITS
            set_current_unit_settings_value(facility_id, current_unit)
            return bundle
        except Exception as e:
            logging.error("CurrentUnitResource.obj_update() exception: %s" % e)
            raise

    def obj_delete_list(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def obj_delete(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def rollback(self, request):
        raise NotImplemented(_("Operation not implemented."))
