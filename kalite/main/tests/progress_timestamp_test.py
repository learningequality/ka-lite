"""
"""
from datetime import datetime

from ..models import ContentLog
from kalite import i18n
from kalite.facility.models import Facility, FacilityUser
from kalite.testing import KALiteClient, KALiteTestCase


class TestSaveContentLog(KALiteTestCase):

    CONTENT_ID = "712f11"
    POINTS = 3
    COMPLETE = True
    COMPLETION_COUNTER = 1
    TIME_SPENT = 11
    PROGRESS_TIMESTAMP = str(datetime.now())
    CONTENT_SOURCE = ""
    CONTENT_KIND = "Document"
    USERNAME = "teststudent"
    PASSWORD = "password"

    def setUp(self):
        super(TestSaveContentLog, self).setUp()
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Default Facility")
        self.facility.save()
        print("==facility", self.facility)
        self.user = FacilityUser(username=self.USERNAME, facility=self.facility)
        self.user.set_password(self.PASSWORD)
        self.user.save()
        print("==user", self.user)

        # create an initial ContentLog instance so we have something to update later
        self.contentlog = ContentLog(content_id=self.CONTENT_ID, user=self.user)
        self.contentlog.points = self.POINTS
        self.contentlog.content_kind = self.CONTENT_KIND,
        self.contentlog.content_source = self.CONTENT_SOURCE
        self.contentlog.save()
        print("==>", self.contentlog)

    def test_new_contentlog(self):
        contentlogs = ContentLog.objects.filter(content_id=self.CONTENT_ID, user__username=self.USERNAME)
        print("===>>>", contentlogs)
        self.assertEqual(contentlogs.count(), 1)