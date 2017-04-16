import glob
import json
import os

from django.db import models

from django.conf import settings
from django.core.urlresolvers import reverse

from securesync.models import DeferredCountSyncedModel
from kalite.facility.models import FacilityUser

from .settings import STUDENT_TESTING_DATA_PATH
from .utils import get_exam_mode_on

# class Test(ExtendedModel):
#   # ids is a JSON serialized list of ids that make up the test.
#   # Field max length set to 15000.
#   # This is greater than a concatenation of all the ids in the current KA exercises set.
#   ids = models.CharField(blank=False, null=False, max_length=15000)
#   # TODO: Field to tie Test to playlists that will be comparable across installations
#   repeats = models.IntegerField(blank=False, null=False, default=1)
#   seed = models.IntegerField(blank=False, null=False, default=1001)
#   title = models.CharField(blank=False, null=False, max_length=200)


class TestLog(DeferredCountSyncedModel):
    user = models.ForeignKey(FacilityUser, blank=False, null=False, db_index=True)
    # test = models.ForeignKey(Test, blank=False, null=False, db_index=True)
    test = models.CharField(blank=False, null=False, max_length=100)
    # TODO: Field that stores the Test/playlist field.
    index = models.IntegerField(blank=False, null=False, default=0)
    complete = models.BooleanField(blank=False, null=False, default=False)
    started = models.BooleanField(blank=False, null=False, default=False)
    total_number = models.IntegerField(blank=False, null=False, default=0)
    total_correct = models.IntegerField(blank=False, null=False, default=0)

    class Meta:  # needed to clear out the app_name property from SyncedClass.Meta
        pass

    def get_test_object(self):
        '''
        Returns the Test object associated with this TestLog.
        '''
        return Test.all(show_all=True)[self.test]

class Test():

    _testscache = {}

    def __init__(self, **kwargs):
        test_id = kwargs.get('test_id')
        self.title = kwargs.get('title')
        self.ids = json.dumps(kwargs.get('ids'))
        self.playlist_ids = json.dumps(kwargs.get('playlist_ids'))
        self.seed = kwargs.get('seed')
        self.repeats = kwargs.get('repeats')
        self.practice = kwargs.get('is_practice')
        self.unit = kwargs.get('unit')
        self.show = kwargs.get('show')
        self.grade = kwargs.get('grade')
        self.test_id = test_id
        self.test_url = "" if settings.CENTRAL_SERVER else reverse('test', args=[test_id])
        self.total_questions = len(kwargs.get('ids', [])) * int(self.repeats or 0)
        self.set_exam_mode()

    def set_exam_mode(self):
        # check if exam mode is active on specific exam
        is_exam_mode = False
        exam_mode_setting = get_exam_mode_on()
        if exam_mode_setting and exam_mode_setting == self.test_id:
            is_exam_mode = True
        self.is_exam_mode = is_exam_mode

    @classmethod
    def all(cls, force=False, show_all=False):
        if "nalanda" not in settings.CONFIG_PACKAGE:
            return {}

        if not cls._testscache or force:
            for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):

                with open(testfile) as f:
                    data = json.load(f)
                    # Coerce each test dict into a Test object
                    # also add in the group IDs that are assigned to view this test
                    test_id = os.path.splitext(os.path.basename(f.name))[0]
                    data["test_id"] = test_id
                    cls._testscache[test_id] = (Test(**data))

        return dict((id, test) for id, test in cls._testscache.iteritems() if show_all or test.show)
