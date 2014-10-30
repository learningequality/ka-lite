"""
These use a web-browser, along with selenium, to simulate user actions.
"""
import time
from django.conf import settings
from django.core.urlresolvers import reverse

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins
from kalite.topic_tools import get_node_cache
from kalite.student_testing.utils import set_current_unit_settings_value

PLAYLIST_ID = "g4_u403_p1"

logging = settings.LOG


class UnitSwitchTest(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):
    """
    Tests that dynamic settings are properly set for different units.
    """
    student_username = 'test_student'
    student_password = 'socrates'
    facility_name = 'facility1'

    def setUp(self):
        """
        Create a student, log the student in.
        """
        super(UnitSwitchTest, self).setUp()
        self.facility = self.create_facility(name=self.facility_name)
        self.student = self.create_student(username=self.student_username, password=self.student_password, facility=self.facility)
        self.browser_login_student(self.student_username, self.student_password, facility_name=self.facility_name)


    def set_unit_navigate_to_exercise(self, unit, exercise_id):
        """
        Set the student unit. Navigate to an exercise.
        """

        set_current_unit_settings_value(self.facility.id, unit)
        self.browse_to(self.live_server_url + get_node_cache("Exercise")[exercise_id][0]["path"])

    def test_nalanda_control_exercise(self):
        """
        Test exercise points in control unit.
        """
        self.set_unit_navigate_to_exercise(1, "place_value")
        time.sleep(5)
        self.assertEqual(self.browser.execute_script("return window.exercise_practice_view.exercise_view.data_model.get('basepoints')"), 0, "Basepoints should be zero in control")

    def test_nalanda_input_exercise(self):
        """
        Test exercise points in input unit.
        """
        self.set_unit_navigate_to_exercise(2, "fractions_on_the_number_line_1")
        time.sleep(5)
        expected_points = self.browser.execute_script("return window.exercise_practice_view.exercise_view.data_model.get('basepoints')")
        self.assertEqual(expected_points, 20, "Basepoints should be 20 in input condition; is actually %s" % expected_points)

    def test_nalanda_output_exercise(self):
        """
        Test exercise points in output unit.
        """
        self.set_unit_navigate_to_exercise(3, "conditional_statements_2")
        time.sleep(5)
        self.assertEqual(self.browser.execute_script("return window.exercise_practice_view.exercise_view.data_model.get('basepoints')"), 0, "Basepoints should be zero in output")

    def test_nalanda_input_video(self):
        """
        Test video points in input unit.
        """
        set_current_unit_settings_value(self.facility.id, 103)
        self.browse_to(
            self.live_server_url +
            reverse("view_playlist", kwargs={"playlist_id": PLAYLIST_ID}))
        time.sleep(5)
        self.assertEqual(self.browser.execute_script("return window.playlist_view.content_view.currently_shown_view.model.get('possible_points')"), 0, "Video points should be zero")
