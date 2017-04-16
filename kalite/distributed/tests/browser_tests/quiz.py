"""
These use a web-browser, along selenium, to simulate user actions.
"""
from django.conf import settings
logging = settings.LOG
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.facility_mixins import FacilityMixins

PLAYLIST_ID = "g3_p1"


@unittest.skipUnless("nalanda" in settings.CONFIG_PACKAGE, "requires Nalanda")
class QuizTest(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):

    """
    Test tests.
    """
    student_username = 'test_student'
    student_password = 'socrates'

    @override_settings(DEBUG=True)
    def setUp(self):
        """
        Create a student, log the student in, and go to the playlist page.
        """
        super(QuizTest, self).setUp()
        self.facility_name = "fac"
        self.facility = self.create_facility(name=self.facility_name)

        self.student_data = {"username": self.student_username,
                             "password": self.student_password}
        self.student = self.create_student(facility=self.facility, **self.student_data)
        self.browser_login_student(
            self.student_username,
            self.student_password,
            facility_name=self.facility_name,
        )

        self.browse_to(
            self.live_server_url +
            reverse("view_playlist", kwargs={"playlist_id": PLAYLIST_ID}))

    def test_quiz_first_answer_correct_not_registered(self):
        """
        Log an answer as correct on a new QuizDataLog Model and check
        that it produces the right values on its total_correct and response_log
        fields.
        """

        self.browser.execute_script("quizlog = new QuizLogModel();")
        self.browser.execute_script("quizlog.add_response_log_item({correct: true});")
        self.assertEqual(self.browser.execute_script("return quizlog.get('total_correct')"), 1)
        self.assertEqual(self.browser.execute_script("return quizlog._response_log_cache[0]"), 1)

