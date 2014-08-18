import glob
import json
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

from .models import TestLog
from .settings import SETTINGS_KEY_EXAM_MODE, STUDENT_TESTING_DATA_PATH
from .utils import get_exam_mode_on, set_exam_mode_on

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
        self.practice = kwargs.get('practice')
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

    #TODO(aron): refactor reading of tests json files
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


SETTINGS_CURRENT_UNIT_PREFIX = 'current_unit_'
SETTINGS_FACILITY_ID_CHARS = 8
SETTINGS_MAX_UNITS = 20  # TODO(cpauya): Maybe put to settings.py or Settings?


# ==========================
# Some helper functions
# ==========================

def _get_current_unit_settings_name(facility_id):
    name = SETTINGS_CURRENT_UNIT_PREFIX
    if facility_id:
        name = "%s%s" % (name, facility_id[:SETTINGS_FACILITY_ID_CHARS],)
    return name


def _set_current_unit_settings_value(facility_id, value):
    """
    Set the value of the current unit on Settings based on the facility id.
    """
    name = _get_current_unit_settings_name(facility_id)
    s = Settings.set(name, value)
    return s


def _get_current_unit_settings_value(facility_id):
    """
    Get value of current unit based on facility id.  If none, defaults to 1 and creates an
    entry on the Settings.
    """
    value = 1
    name = _get_current_unit_settings_name(facility_id)
    value = Settings.get(name, value)
    return value


# ==========================
# TastyPie classes
# ==========================

class CurrentUnit():
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', '<id>')
        self.facility_id = kwargs.get('facility_id', '')
        self.facility_name = kwargs.get('facility_name', '<facility_name>')
        self.facility_url = kwargs.get('facility_url', '<facility_url>')
        self.unit_list = kwargs.get('unit_list', self._get_unit_list())
        self.current_unit = kwargs.get('current_unit', self._get_current_unit())
        self.is_on_first = self.current_unit <= 1
        if self.unit_list and self.current_unit:
            is_on_last = self.unit_list[len(self.unit_list)-1] <= self.current_unit
            self.is_on_last = is_on_last

    def __unicode__(self):
        return self.facility_name

    def _get_settings_name(self):
        name = _get_current_unit_settings_name(self.facility_id)
        return name

    def _get_settings_value(self):
        value = _get_current_unit_settings_value(self.facility_id)
        return value

    def _get_current_unit(self):
        # TODO(cpauya): get active unit for the Facility from Settings, randomize for now
        current_unit = 0
        if self.facility_id:
            current_unit = self._get_settings_value()
        else:
            if self.unit_list:
                current_unit = randint(1, len(self.unit_list))
        return current_unit

    def _get_unit_list(self):
        # TODO(cpauya): Return list of units, facility_id can be passed later to determine list of units
        # for the facility.
        l = [x for x in xrange(1, SETTINGS_MAX_UNITS + 1)]
        return l


@api_handle_error_with_json
class CurrentUnitResource(Resource):

    id = fields.CharField(attribute='id')
    facility_id = fields.CharField(attribute='facility_id')
    facility_name = fields.CharField(attribute='facility_name')
    facility_url = fields.CharField(attribute='facility_url')
    current_unit = fields.CharField(attribute='current_unit')
    is_on_first = fields.BooleanField(attribute='is_on_first', default=False)
    is_on_last = fields.BooleanField(attribute='is_on_last', default=False)
    unit_list = fields.ListField(attribute='unit_list')

    class Meta:
        resource_name = 'current_unit'
        object_class = CurrentUnit

    def obj_get_list(self, bundle, **kwargs):
        """
        Get the list of facilities based from a request.
        """
        l = []
        if bundle.request.is_admin:
            # TODO(cpauya): get facilities for current user
            facilities = Facility.objects.order_by('name')
            for facility in facilities:
                url = reverse('facility_management', args=[None, facility.id])
                o = CurrentUnit(
                    id=facility.id,
                    facility_id=facility.id,
                    facility_name=facility.name,
                    facility_url=url
                )
                l.append(o)
            return l
        raise Unauthorized(_("You cannot view these objects."))

    def get_object_list(self, request, force=False):
        raise NotImplemented(_("Operation not implemented."))

    def obj_create(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def obj_update(self, bundle, **kwargs):
        if not bundle.request.is_admin:
            raise Unauthorized(_("You cannot update this object."))
        try:
            # raise Exception('==> TODO(cpauya): remove when done testing')
            # logging.warning('==> obj_update kwargs == %s; bundle == %s' % (kwargs, bundle.data,))
            is_next = bundle.data.get('is_next', False)
            is_previous = bundle.data.get('is_previous', False)
            facility_id = bundle.data.get('facility_id', '')
            current_unit = bundle.data.get('current_unit', '')
            selected_unit = int(bundle.data.get('selected_unit', '0'))
            # logging.warning('==> obj_update %s -- %s -- %s' % (facility_id, current_unit, selected_unit,))
            if current_unit:
                current_unit = int(current_unit)
                if selected_unit and 1 <= selected_unit <= SETTINGS_MAX_UNITS:
                    current_unit = selected_unit
                elif is_next and current_unit < SETTINGS_MAX_UNITS:
                    current_unit += 1
                elif is_previous and current_unit > 1:
                    current_unit -= 1
                else:
                    current_unit = 1
                _set_current_unit_settings_value(facility_id, current_unit)
            return bundle
        except Exception as e:
            logging.error("CurrentUnitResource exception: %s" % e)
            pass
        raise NotImplemented(_("Operation not implemented."))

    def obj_delete_list(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def obj_delete(self, request):
        raise NotImplemented(_("Operation not implemented."))

    def rollback(self, request):
        raise NotImplemented(_("Operation not implemented."))
