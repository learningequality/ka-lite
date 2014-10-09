"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui

from django.conf import settings
from django.utils import unittest
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from fle_utils.general import isnumeric
from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, FacilityMixins
from kalite.topic_tools import get_exercise_paths, get_node_cache

logging = settings.LOG


class TestAddFacility(BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase):
    """
    Test webpage for adding a facility
    """

    def test_browser_add_facility(self, facility_name="My Test Facility"):
        """Add a facility"""

        self.admin_data = {"username": "admin", "password": "admin"}
        self.create_admin(**self.admin_data)

        # Login as admin
        self.browser_login_admin(**self.admin_data)

        params = {
            "zone_id": None,
        }
        # Add the facility
        add_facility_url = self.reverse("add_facility", kwargs=params)
        self.browse_to(add_facility_url)

        self.browser_activate_element(id="id_name") # explicitly set the focus, to start
        self.browser_send_keys(facility_name)
        self.browser.find_elements_by_class_name("submit")[0].click()
        self.wait_for_page_change(add_facility_url)

        self.browser_check_django_message(message_type="success", contains="has been successfully saved!")


class DeviceUnregisteredTest(BrowserActionMixins, KALiteBrowserTestCase):
    """Validate all the steps of registering a device.

    Currently, only testing that the device is not registered works.
    """

    @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    def test_device_unregistered(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """
        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browse_to(home_url) # Load page
        self.browser_check_django_message(message_type="warning", contains="complete the setup.")
        self.assertFalse(self.browser_is_logged_in(), "Not (yet) logged in")

        # Now, log in as admin
        self.browser_login_admin()


@unittest.skipIf(settings.DISABLE_SELF_ADMIN, "Registration not allowed when DISABLE_SELF_ADMIN set.")
class UserRegistrationCaseTest(BrowserActionMixins, KALiteBrowserTestCase):
    username = "user1"
    password = "password"

    def test_register_login_exact(self):
        """Tests that a user can login with the exact same email address as registered"""

        # Register user in one case
        self.browser_register_user(username=self.username.lower(), password=self.password)

        # Login in the same case
        self.browser_login_student(username=self.username.lower(), password=self.password)
        self.browser_logout_user()

    def test_login_mixed(self):
        """Tests that a user can login with the uppercased version of the email address that was registered"""
        # Register user in one case
        self.browser_register_user(username=self.username.lower(), password=self.password)

        # Login in the same case
        self.browser_login_student(username=self.username.upper(), password=self.password)
        self.browser_logout_user()

    @unittest.skipIf(True, "Waiting for Dylan's fix for the Sign Up redirect")
    def test_register_mixed(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""

        # Register user in one case
        self.browser_register_user(username=self.username.lower(), password=self.password)

        # Try to register again in a different case
        self.browser_register_user(username=self.username.upper(), password=self.password)

        text_box = self.browser.find_element_by_id("id_username") # form element
        error = text_box.parent.find_elements_by_class_name("errorlist")[-1]
        self.assertIn(_("A user with this username already exists."), error.text, "Check 'username is taken' error.")

    @unittest.skipIf(True, "Waiting for Dylan's fix for the Sign Up redirect loop")
    def test_login_two_users_different_cases(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""

        user1_uname = self.username.lower()
        user2_uname = "a"+self.username.lower()
        user1_password = self.password
        user2_password = "a"+self.password
        user1_fname = "User1"
        user2_fname = "User2"

        # Register & activate two users with different usernames / emails
        self.browser_register_user(username=user1_uname, password=user1_password, first_name=user1_fname)
        self.browser_login_student(username=user1_uname, password=user1_password)
        self.browser_logout_user()

        self.browser_register_user(username=user2_uname, password=user2_password, first_name=user2_fname)
        self.browser_login_student(username=user2_uname, password=user2_password)
        self.browser_logout_user()

        # Change the second user to be a case-different version of the first user
        user2 = FacilityUser.objects.get(username=user2_uname)
        user2_uname = user1_uname.upper()
        user2.username = user2_uname
        user2.email = user2_uname
        user2.save()

        # First, make sure that user 1 can only log in with user 1's email/password
        self.browser_login_student(username=user1_uname, password=user1_password) # succeeds
        self.browser_logout_user()
        self.browser_login_student(username=user2_uname, password=user1_password) # fails
        self.browser_check_django_message("error", contains="There was an error logging you in.")

        # Now, check the same in the opposite direction.
        self.browser_login_student(username=user2_uname, password=user2_password) # succeeds
        self.browser_logout_user()

        self.browser_login_student(username=user1_uname, password=user2_password) # fails
        self.browser_check_django_message("error", contains="There was an error logging you in.")


@unittest.skipIf(getattr(settings, 'HEADLESS', None), "Fails if settings.HEADLESS is set.")
class StudentExerciseTest(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):
    """
    Test exercises.
    """
    student_username = 'test_student'
    student_password =  'socrates'
    EXERCISE_SLUG = 'addition_1'
    MIN_POINTS = get_node_cache("Exercise")[EXERCISE_SLUG]["basepoints"]
    MAX_POINTS = 2 * MIN_POINTS

    def setUp(self):
        """
        Create a student, log the student in, and go to the exercise page.
        """
        super(StudentExerciseTest, self).setUp()
        self.facility_name = "fac"
        self.facility = self.create_facility(name=self.facility_name)
        self.student = self.create_student(username=self.student_username,
                                           password=self.student_password,
                                           facility=self.facility)
        self.browser_login_student(self.student_username, self.student_password, facility_name=self.facility_name)

        self.browse_to(self.live_server_url + get_node_cache("Exercise")[self.EXERCISE_SLUG]["path"])
        self.nanswers = self.browser.execute_script('return window.ExerciseParams.STREAK_CORRECT_NEEDED;')

    def browser_get_current_points(self):
        """
        Check the total points a student has accumulated, from an exercise page.
        """
        try:
            points_regexp = r'\((?P<points>\w+) points\)'
            points_text = self.browser.find_element_by_css_selector('.progress-points').text
            points = re.match(points_regexp, points_text).group('points')
            return points
        except AttributeError:
            return ""

    def browser_submit_answer(self, answer):
        """
        From an exercise page, insert an answer into the text box and submit.
        """
        self.browser.find_element_by_id('solutionarea').find_element_by_css_selector('input[type=text]').click()
        self.browser_send_keys(unicode(answer))
        self.browser_send_keys(Keys.RETURN)

        # Convert points to a number, when appropriate
        time.sleep(0.25)
        points = self.browser_get_current_points()
        return float(points) if isnumeric(points) else points

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    def test_question_correct_points_are_added(self):
        """
        Answer an exercise correctly
        """
        numbers = self.browser.find_elements_by_class_name('mn')
        answer = sum(int(num.text) for num in numbers)
        points = self.browser_submit_answer(answer)
        self.assertTrue(self.MIN_POINTS <= points <= self.MAX_POINTS,
                        "point update is wrong: %s. Should be %s <= points <= %s" % (points,
                                                                                     self.MIN_POINTS,
                                                                                     self.MAX_POINTS))

        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 100 / self.nanswers, "Streak progress should be 10%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, 1, "Student should have 1 attempt.")
        self.assertFalse(elog.complete, "Student should not have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, None, "Student should not have a value for attempts_before_completion.")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    def test_question_incorrect_no_points_are_added(self):
        """
        Answer an exercise incorrectly.
        """
        points = self.browser_submit_answer('this is a wrong answer')
        self.assertEquals(points, "", "points text should be empty")

        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 0, "Streak progress should be 0%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, 1, "Student should have 1 attempt.")
        self.assertFalse(elog.complete, "Student should not have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, None, "Student should not have a value for attempts_before_completion.")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    def test_question_incorrect_button_text_changes(self):
        """
        Answer an exercise incorrectly, and make sure button text changes.
        """
        self.browser_submit_answer('this is a wrong answer')

        answer_button_text = self.browser.find_element_by_id("check-answer-button").get_attribute("value")

        self.assertTrue(answer_button_text == "Try Again!", "Answer button did not change to 'Try Again' on incorrect answer!")

    # @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    @override_settings(CONFIG_PACKAGE=None)
    def test_exercise_mastery(self):
        """
        Answer an exercise til mastery
        """
        points = 0
        for ai in range(1, 1 + self.nanswers):
            # Hey future maintainer! The visibility_of_element_located
            # requires that the element be ACTUALLY visible on the screen!
            # so you can't just have the test spawn a teeny-bitty browser to
            # the side while you have the world cup occupying a big part of your
            # screen.
            ui.WebDriverWait(self.browser, 10).until(
                expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'mn'))
            )
            numbers = self.browser.find_elements_by_class_name('mn')
            answer = sum(int(num.text) for num in numbers)
            expected_min_points = points + self.MIN_POINTS
            expected_max_points = points + self.MAX_POINTS
            points = self.browser_submit_answer(answer)
            self.assertGreaterEqual(points, expected_min_points, "Too few points were given: %s < %s" % (points,
                                                                                                         expected_min_points))
            self.assertLessEqual(points, expected_max_points, "Too many points were given: %s > %s" % (points,
                                                                                                       expected_max_points))

            self.browser_send_keys(Keys.RETURN)  # move on to next question.

        # Now test the models
        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 100, "Streak progress should be 100%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, self.nanswers, "Student should have %s attempts. Got %s" % (self.nanswers, elog.attempts))
        self.assertTrue(elog.complete, "Student should have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, self.nanswers, "Student should have %s attempts for completion." % self.nanswers)


@unittest.skipIf("medium" in settings.TESTS_TO_SKIP, "Skipping medium-length test")
class LoadExerciseTest(BrowserActionMixins, KALiteBrowserTestCase):
    """Tests if the exercise is loaded without any JS error.

    The test is run over all urls and check for any JS error.
    """
    student_username = 'test_student'
    student_password =  'socrates'

    def setUp(self):
        super(LoadExerciseTest, self).setUp()
        self.student = self.create_student()
        self.browser_login_student(self.student_username, self.student_password)

    def test_get_exercise_load_status(self):
        for path in get_exercise_paths():
            logging.debug("Testing path : " + path)
            self.browser.get(self.live_server_url + path)
            error_list = self.browser.execute_script("return window.js_errors;")
            if error_list:
                logging.error("Found JS error(s) while loading path: " + path)
                for e in error_list:
                    logging.error(e)
            self.assertFalse(error_list)


class MainEmptyFormSubmitCaseTest(CreateAdminMixin, BrowserActionMixins, KALiteBrowserTestCase):
    """
    Submit forms with no values, make sure there are no errors.

    Note: these are functions on securesync, but
    """

    def setUp(self):
        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        super(MainEmptyFormSubmitCaseTest, self).setUp()

    def test_login_form(self):
        self.empty_form_test(url=self.reverse("login"), submission_element_id="id_username")

    def test_add_student_form(self):
        self.empty_form_test(url=self.reverse("add_facility_student"), submission_element_id="id_username")

    def test_add_teacher_form(self):
        self.empty_form_test(url=self.reverse("add_facility_teacher"), submission_element_id="id_username")

    def test_add_group_form(self):
        self.browser_login_admin(**self.admin_data)
        self.empty_form_test(url=self.reverse("add_group"), submission_element_id="id_name")


@override_settings(SESSION_IDLE_TIMEOUT=1)
class TestSessionTimeout(CreateAdminMixin, BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):
    """
    Test webpage for timing out user sessions
    """

    def test_facility_user_logout_after_interval(self):
        """Students should be auto-logged out"""
        student_username = 'test_student'
        student_password =  'socrates'
        self.student = self.create_student(username=student_username, password=student_password)
        self.browser_login_student(student_username, student_password)
        time.sleep(3)
        self.browse_to(self.reverse("exercise_dashboard"))
        self.browser_check_django_message(message_type="error", contains="Your session has been timed out.")

    def test_admin_no_logout_after_interval(self):
        """Admin should not be auto-logged out"""
        admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**admin_data)
        self.browser_login_admin(**admin_data)
        time.sleep(3)
        self.browse_to(self.reverse("homepage"))
        self.assertTrue(self.browser_is_logged_in(), "Timeout should not logout admin")
        
    def test_teacher_no_logout_after_interval(self):
        """Teacher should not be auto-logged out"""
        self.teacher = self.create_teacher()
        self.browser_login_teacher(username=self.teacher.username, password="password")
        time.sleep(3)
        self.browse_to(self.reverse("homepage"))
        self.assertTrue(self.browser_is_logged_in(), "Timeout should not logout teacher")
