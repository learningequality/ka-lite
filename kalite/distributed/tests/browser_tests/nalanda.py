"""
These use a web-browser, along with selenium, to simulate user actions.
"""
import time
from django.conf import settings
from django.core.urlresolvers import reverse

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins
from kalite.topic_tools import get_node_cache

logging = settings.LOG


class ExerciseTest(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):

    student_username = 'test_student'
    student_password = 'socrates'
    facility_name = 'facility1'

    def setUp(self):
        """
        Create a student, log the student in.
        """
        super(ExerciseTest, self).setUp()
        self.facility = self.create_facility(name=self.facility_name)
        self.student = self.create_student(username=self.student_username, password=self.student_password, facility=self.facility)
        self.browser_login_student(self.student_username, self.student_password, facility_name=self.facility_name)


    def set_navigate_to_exercise(self, exercise_id):
        """
        Navigate to an exercise.
        """
        self.browse_to(self.live_server_url + get_node_cache("Exercise")[exercise_id][0]["path"])


    def test_exercise_points(self):
        """
        Test exercise points.
        """
        self.set_navigate_to_exercise("telling_time")
        time.sleep(5)
        actual_points = self.browser.execute_script("return window.exercise_practice_view.exercise_view.data_model.get('basepoints')")
        expected_points = 25
        self.assertEqual(actual_points, expected_points, "Basepoints should be %s in input condition; is actually %s" % (expected_points, actual_points))
