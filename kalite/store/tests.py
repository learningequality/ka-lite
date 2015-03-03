from django.conf import settings
from django.test.utils import override_settings

from kalite.testing.base import KALiteTestCase
from kalite.testing.client import KALiteClient
from kalite.testing.mixins.facility_mixins import FacilityMixins, CreateTeacherMixin, CreateStudentMixin

from kalite.main.models import ExerciseLog

from kalite.student_testing.models import Test, TestLog
from kalite.student_testing.utils import set_exam_mode_on

from .models import StoreTransactionLog, playlist_group_mapping_reset_for_a_facility

logging = settings.LOG


class BaseTest(FacilityMixins, KALiteTestCase):

    client_class = KALiteClient

    exam_id = 'g4_u404_t4_practice'

    def setUp(self):

        super(BaseTest, self).setUp()
        self.facility = self.create_facility(name="facility1")
        self.teacher_data = CreateTeacherMixin.DEFAULTS.copy()
        self.student_data = CreateStudentMixin.DEFAULTS.copy()
        self.teacher_data['facility'] = self.student_data['facility'] = self.facility

        self.teacher = self.create_teacher(**self.teacher_data)
        self.student = self.create_student(**self.student_data)


class SwitchTest(BaseTest):

    def setUp(self):
        super(SwitchTest, self).setUp()

    def tearDown(self):
        super(SwitchTest, self).tearDown()

        StoreTransactionLog.objects.all().soft_delete()

    @override_settings(CONFIG_PACKAGE=["Nalanda"])
    def test_playlist_group_mapping_reset_for_a_facility(self):
        from kalite.playlist.models import PlaylistToGroupMapping
        from kalite.facility.models import FacilityGroup
        group = FacilityGroup.objects.create(name='testgroup', facility=self.facility)
        PlaylistToGroupMapping(playlist= "Playlist 1", group = group).save()
        previous_count = PlaylistToGroupMapping.objects.count()
        playlist_group_mapping_reset_for_a_facility(self.facility.id)
        new_count = PlaylistToGroupMapping.objects.count()
        self.assertTrue(previous_count > new_count)
