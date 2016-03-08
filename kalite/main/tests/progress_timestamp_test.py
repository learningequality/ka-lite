"""
"""

from ..models import ContentLog
from kalite.facility.models import Facility, FacilityUser
from kalite.testing.base import KALiteTestCase


class TestSaveContentLog(KALiteTestCase):

    CONTENT_ID = "712f11"
    POINTS = 3
    COMPLETION_COUNTER = 1
    CONTENT_SOURCE = ""
    CONTENT_KIND = "Document"
    USERNAME = "teststudent"
    PASSWORD = "password"

    def setUp(self):
        super(TestSaveContentLog, self).setUp()
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Default Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.USERNAME, facility=self.facility)
        self.user.set_password(self.PASSWORD)
        self.user.save()

        # create an initial ContentLog instance so we have something to update later
        self.contentlog = ContentLog(content_id=self.CONTENT_ID, user=self.user)
        self.contentlog.points = self.POINTS
        self.contentlog.content_kind = self.CONTENT_KIND
        self.contentlog.content_source = self.CONTENT_SOURCE
        self.contentlog.save()

    def test_timestamp(self):
            new_start_timestamp = ContentLog.objects.get(user=self.user)
            new_start_timestamp.save()
            # Make sure that the start_timestamp will not change when we update,
            # only progress_timestamp will update.
            self.assertEqual(new_start_timestamp.start_timestamp, self.contentlog.start_timestamp)
            self.assertTrue(new_start_timestamp.progress_timestamp > self.contentlog.progress_timestamp)