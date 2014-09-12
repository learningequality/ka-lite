from django.conf import settings
from django.test.utils import override_settings

from kalite.testing.base import KALiteTestCase
from kalite.testing.client import KALiteClient
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin

from kalite.main.models import ExerciseLog

from kalite.student_testing.models import Test, TestLog
from kalite.student_testing.utils import set_exam_mode_on, set_current_unit_settings_value

from .models import StoreTransactionLog

logging = settings.LOG

class BaseTest(FacilityMixins, CreateDeviceMixin, KALiteTestCase):

    client_class = KALiteClient

    exam_id = 'g4_t1_practice'

    def setUp(self):

        super(BaseTest, self).setUp()

        # make tests faster
        self.setup_fake_device()

        self.client.setUp()
        self.assertTrue(self.client.facility)
        self.assertTrue(self.client.teacher)
        self.assertTrue(self.client.student)


class SwitchTest(BaseTest):

    def setup(self):
        super(SwitchTest, self).setUp()

        set_current_unit_settings_value(self.client.facility.id, 1)

    def tearDown(self):
        super(SwitchTest, self).tearDown()

        StoreTransactionLog.objects.all().soft_delete()

    @override_settings(CONFIG_PACKAGE=["Nalanda"])
    def test_exam_unset(self):
        """
        Tests that when an exam is unset in the output condition
        that a gift_card is created with appropriate points.
        """
        test_object = Test.all().get(self.exam_id, None)
        self.assertTrue(test_object)
        testlog = TestLog(user=self.client.student, test=self.exam_id, index=20, started=True, complete=True, total_correct=10, total_number=20)
        testlog.save()
        # Set to unit 3 for output condition for facility1.
        set_current_unit_settings_value(self.client.facility.id, 3)
        # Set and unset exam mode to trigger signal.
        set_exam_mode_on(test_object)
        set_exam_mode_on(test_object)
        transactionlogs = StoreTransactionLog.objects.filter(user=self.client.student, context_id="3", context_type="output_condition", item="gift_card")
        self.assertTrue(len(transactionlogs))
        for transactionlog in transactionlogs:
            self.assertTrue(transactionlog.value==int(round(settings.UNIT_POINTS*float(testlog.total_correct)/testlog.total_number)))


    @override_settings(CONFIG_PACKAGE=["Nalanda"])
    def test_unit_switch(self):
        """
        Tests that when a unit is switched a negative value gift_card
        is created to nullify current user points.
        """
        set_current_unit_settings_value(self.client.facility.id, 2)

        exerciselog = ExerciseLog(user=self.client.student, exercise_id="addition_1", streak_progress=8, attempts=8, points=10, complete=True)
        exerciselog.save()

        # Set to unit 3 to trigger signal.
        set_current_unit_settings_value(self.client.facility.id, 3)

        transactionlogs = StoreTransactionLog.objects.filter(user=self.client.student, context_id="2", context_type="unit_points_reset", item="gift_card")
        self.assertTrue(len(transactionlogs)==1)

        for transactionlog in transactionlogs:
            self.assertTrue(transactionlog.value==-exerciselog.points)

        newexerciselog = ExerciseLog(user=self.client.student, exercise_id="addition_2", streak_progress=8, attempts=8, points=20, complete=True)
        newexerciselog.save()

        # Move back a unit
        set_current_unit_settings_value(self.client.facility.id, 2)

        # Check that newexerciselog has been nullified
        transactionlogs = StoreTransactionLog.objects.filter(user=self.client.student, context_id="3", context_type="unit_points_reset", item="gift_card")
        self.assertTrue(len(transactionlogs)==1)
        for transactionlog in transactionlogs:
            self.assertTrue(transactionlog.value==-newexerciselog.points)

        # Check that the original transactionlog has been deleted
        transactionlogs = StoreTransactionLog.objects.filter(user=self.client.student, context_id="2", context_type="unit_points_reset", item="gift_card")
        self.assertTrue(len(transactionlogs)==0)