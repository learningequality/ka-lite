"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.webdriver.firefox.webdriver import WebDriver

from django.conf import settings; logging = settings.LOG
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from django.utils.translation import ugettext as _

from fle_utils.django_utils import call_command_with_output
from fle_utils.general import isnumeric
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.main.models import ExerciseLog
from kalite.main.topic_tools import get_exercise_paths, get_node_cache
from kalite.testing.browser import BrowserTestCase


class KALiteDistributedBrowserTestCase(BrowserTestCase):
    """Base class for main server test cases.
    They will have different functions in here, for sure.
    """

    default_username = "test_student"
    default_password = "socrates"
    default_facility_name = "middle of nowhere"

    def tearDown(self):
        """
        """

        # Must clean up, as browser sessions could persist
        if self.persistent_browser:
            self.browser_logout_user()
        super(KALiteDistributedBrowserTestCase, self).tearDown()

    def create_student(self, username=default_username, password=default_password, facility_name=default_facility_name):
        facilities = Facility.objects.filter(name=facility_name)
        facility = facilities[0] if facilities else self.create_facility()
        student = FacilityUser(username=username, facility=facility)
        student.set_password(raw_password=password)
        student.save()

        return student

    def create_facility(self, facility_name=default_facility_name):
        if Facility.objects.filter(name=facility_name):
            logging.debug("Creating duplicate facility: %s" % facility_name)
        facility = Facility(name=facility_name)
        facility.save()
        return facility

    def browser_register_user(self, username, password, first_name="firstname", last_name="lastname", facility_name=None, stay_logged_in=False, expect_success=True):
        """Tests that a user can register"""

        # Expected results vary based on whether a user is logged in or not.
        if not stay_logged_in:
            self.browser_logout_user()

        register_url = self.reverse("add_facility_student")
        self.browse_to(register_url) # Load page
        #self.assertIn(_("Sign up"), self.browser.title, "Register page title") # this depends on who is logged in.

        # Part 1: REGISTER
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)
        self.browser_activate_element(id="id_username") # explicitly set the focus, to start
        self.browser_form_fill(username) # first name
        self.browser_form_fill(first_name) # first name
        self.browser_form_fill(last_name) # last name
        self.browser_form_fill(password) #password
        self.browser_form_fill(password) #password (again)
        self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(register_url), "RETURN causes page to change")
            self.assertIn(reverse("login"), self.browser.current_url, "Register browses to login page" )
            #self.browser_check_django_message(message_type="success", contains="You successfully registered.")
            # uncomment message check when that code gets checked in

    def browser_login_user(self, username, password, facility_name=None, expect_success=True):
        """
        Tests that an existing admin user can log in.
        """

        login_url = self.reverse("login")
        self.browse_to(login_url) # Load page
        self.assertIn(_("Log in"), self.browser.title, "Login page title")

        # Focus should be on username, password and submit
        #   should be accessible through keyboard only.
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)

        self.browser.find_element_by_id("id_username").clear() # clear any data
        self.browser.find_element_by_id("id_username").click() # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(password)
        self.browser_send_keys(Keys.RETURN)

        # Make sure that the page changed to the admin homepage
        if expect_success:
            self.assertTrue(self.wait_for_page_change(login_url), "RETURN causes page to change")
            time.sleep(0.5)  # allow async status to update
            self.assertTrue(self.browser_is_logged_in(username), "make sure %s is logged in." % username)


    def browser_login_admin(self, username=None, password=None, expect_success=True):
        if username is None:
            username = self.admin_user.username
        if password is None:
            password = self.admin_pass

        self.browser_login_user(username=username, password=password, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("zone_management", kwargs={"zone_id": "None"}), self.browser.current_url, "Login browses to zone_management page" )

    def browser_login_teacher(self, username, password, facility_name=None, expect_success=True):
        self.browser_login_user(username=username, password=password, facility_name=facility_name, expect_success=expect_success)
        if expect_success:
            self.assertIn(reverse("coach_reports"), self.browser.current_url, "Login browses to coach reports page" )
            self.browser_check_django_message("success", contains="You've been logged in!")

    def browser_login_student(self, username, password, facility_name=None, expect_success=True):
        self.browser_login_user(username=username, password=password, facility_name=facility_name, expect_success=expect_success)
        time.sleep(self.max_wait_time/10) # allow time for async messages to load
        if expect_success:
            self.assertIn(reverse("homepage"), self.browser.current_url, "Login browses to homepage" )
            self.browser_check_django_message("success", contains="You've been logged in!")

    def browser_logout_user(self):
        if self.browser_is_logged_in():
            # Since logout redirects to the homepage, browse_to will fail (with no good way to avoid).
            #   so be smarter in that case.
            if self.reverse("homepage") in self.browser.current_url:
                self.browser.get(self.reverse("logout"))
            else:
                self.browse_to(self.reverse("logout"))
            self.assertIn(reverse("homepage"), self.browser.current_url, "Logout browses to homepage" )
            self.assertFalse(self.browser_is_logged_in(), "Make sure that user is no longer logged in.")

    def browser_is_logged_in(self, expected_username=None):
        # Two ways to be logged in:
        # 1. Student: #logged-in-name is username
        # 2. Admin: #logout contains username
        try:
            logged_in_name_text = self.browser.find_element_by_id("logged-in-name").text.strip()
            logout_text = self.browser.find_element_by_id("nav_logout").text.strip()
        except NoSuchElementException:
            # We're on an unrecognized webpage
            return False

        username_text = logged_in_name_text or logout_text[0:-len(" (%s)" % _("Logout"))]

        # Just checking to see if ANYBODY is logged in
        if not expected_username:
            return username_text != ""
        # Checking to see if Django user, or user with missing names is logged in
        #   (then username displays)
        elif username_text.lower() == expected_username.lower():
            return True
        # Checking to see if a FacilityUser with a filled-in-name is logged in
        else:
            user_obj = FacilityUser.objects.filter(username=expected_username)
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()

            user_obj = FacilityUser.objects.filter(username__iexact=expected_username)
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()
            else:
                assert username_text == "", "Impossible for anybody to be logged in."


class KALiteDistributedWithFacilityBrowserTestCase(KALiteDistributedBrowserTestCase):
    """
    Same thing, but do the setup steps to register a facility.
    """
    facility_name = 'middle of nowhere'

    def setUp(self):
        """Add a facility, so users can begin registering / logging in immediately."""
        super(KALiteDistributedWithFacilityBrowserTestCase,self).setUp() # sets up admin, etc
        self.facility = self.create_facility(facility_name=self.facility_name)


class TestAddFacility(KALiteDistributedBrowserTestCase):
    """
    Test webpage for adding a facility
    """

    def test_browser_add_facility(self, facility_name="My Test Facility"):
        """Add a facility"""

        # Login as admin
        self.browser_login_admin()

        # Add the facility
        add_facility_url = self.reverse("add_facility", kwargs={"id": "new"})
        self.browse_to(add_facility_url)

        self.browser_activate_element(id="id_name") # explicitly set the focus, to start
        self.browser_send_keys(facility_name)
        self.browser.find_elements_by_class_name("submit")[0].click()
        self.wait_for_page_change(add_facility_url)

        self.browser_check_django_message(message_type="success", contains="has been successfully saved!")


class DeviceUnregisteredTest(KALiteDistributedBrowserTestCase):
    """Validate all the steps of registering a device.

    Currently, only testing that the device is not registered works.
    """

    def test_device_unregistered(self):
        """
        Tests that a device is initially unregistered, and that it can
        be registered through automatic means.
        """
        home_url = self.reverse("homepage")

        # First, get the homepage without any automated information.
        self.browser.get(home_url) # Load page
        self.browser_check_django_message(message_type="warning", contains="complete the setup.")
        self.assertFalse(self.browser_is_logged_in(), "Not (yet) logged in")

        # Now, log in as admin
        self.browser_login_admin()


@unittest.skipIf(settings.DISABLE_SELF_ADMIN, "Registration not allowed when DISABLE_SELF_ADMIN set.")
class UserRegistrationCaseTest(KALiteDistributedWithFacilityBrowserTestCase):
    username   = "user1"
    password   = "password"

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


    def test_register_mixed(self):
        """Tests that a user cannot re-register with the uppercased version of an email address that was registered"""

        # Register user in one case
        self.browser_register_user(username=self.username.lower(), password=self.password)

        # Try to register again in a different case
        self.browser_register_user(username=self.username.upper(), password=self.password, expect_success=False)

        text_box = self.browser.find_element_by_id("id_username") # form element
        error    = text_box.parent.find_elements_by_class_name("errorlist")[-1]
        self.assertIn(_("A user with this username already exists."), error.text, "Check 'username is taken' error.")


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
        self.browser_login_student(username=user2_uname, password=user1_password, expect_success=False) # fails
        self.browser_check_django_message("error", contains="There was an error logging you in.")

        # Now, check the same in the opposite direction.
        self.browser_login_student(username=user2_uname, password=user2_password) # succeeds
        self.browser_logout_user()

        self.browser_login_student(username=user1_uname, password=user2_password, expect_success=False) # fails
        self.browser_check_django_message("error", contains="There was an error logging you in.")


class StudentExerciseTest(KALiteDistributedWithFacilityBrowserTestCase):
    """
    Test exercises.
    """
    student_username = 'test_student'
    student_password =  'socrates'
    EXERCISE_SLUG = 'addition_1'
    MIN_POINTS = get_node_cache("Exercise")[EXERCISE_SLUG][0]["basepoints"]
    MAX_POINTS = 2 * MIN_POINTS

    def setUp(self):
        """
        Create a student, log the student in, and go to the exercise page.
        """
        super(StudentExerciseTest, self).setUp()
        self.student = self.create_student(facility_name=self.facility_name)
        self.browser_login_student(self.student_username, self.student_password, facility_name=self.facility_name)

        self.browse_to(self.live_server_url + get_node_cache("Exercise")[self.EXERCISE_SLUG][0]["path"])
        self.browser_check_django_message(num_messages=0)  # make sure no messages

    def browser_get_current_points(self):
        """
        Check the total points a student has accumulated, from an exercise page.
        """
        return self.browser.find_element_by_css_selector('#totalpoints').text

    def browser_submit_answer(self, answer):
        """
        From an exercise page, insert an answer into the text box and submit.
        """
        self.browser.find_element_by_css_selector('#solutionarea input[type=text]').click()
        self.browser_send_keys(unicode(answer))
        self.browser_send_keys(Keys.RETURN)

        # Convert points to a number, when appropriate
        time.sleep(0.25)
        points = self.browser_get_current_points()
        return float(points) if isnumeric(points) else points

    def test_question_correct_points_are_added(self):
        """
        Answer an exercise correctly
        """
        numbers = self.browser.find_elements_by_class_name('mn')
        answer = sum(int(num.text) for num in numbers)
        points = self.browser_submit_answer(answer)
        self.assertTrue(self.MIN_POINTS <= points <= self.MAX_POINTS, "point update is wrong: %s. Should be %s <= points <= %s" % (points, self.MIN_POINTS, self.MAX_POINTS))
        self.browser_check_django_message(num_messages=0)  # make sure no messages

        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 10, "Streak progress should be 10%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, 1, "Student should have 1 attempt.")
        self.assertFalse(elog.complete, "Student should not have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, None, "Student should not have a value for attempts_before_completion.")

    def test_question_incorrect_no_points_are_added(self):
        """
        Answer an exercise incorrectly.
        """
        points = self.browser_submit_answer('this is a wrong answer')
        self.assertEqual(points, "", "points text should be empty")
        self.browser_check_django_message(num_messages=0)  # make sure no messages

        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 0, "Streak progress should be 0%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, 1, "Student should have 1 attempt.")
        self.assertFalse(elog.complete, "Student should not have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, None, "Student should not have a value for attempts_before_completion.")

    def test_exercise_mastery(self):
        """
        Answer an exercise 10 times correctly; verify mastery message
        """
        points = 0
        nanswers = 10
        for ai in range(1,1 + nanswers):
            numbers = self.browser.find_elements_by_class_name('mn')
            answer = sum(int(num.text) for num in numbers)
            expected_min_points = points + self.MIN_POINTS
            expected_max_points = points + self.MAX_POINTS
            points = self.browser_submit_answer(answer)
            self.assertGreaterEqual(points, expected_min_points, "Too few points were given: %s < %s" % (points, expected_min_points))
            self.assertLessEqual(points, expected_max_points, "Too many points were given: %s > %s" % (points, expected_max_points))
            if ai < nanswers:
                self.browser_check_django_message(num_messages=0)  # make sure no messages
            else:
                self.browser_check_django_message(message_type="success", contains="You have mastered this exercise!")
            self.browser_send_keys(Keys.RETURN)  # move on to next question.

        # Now test the models
        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 100, "Streak progress should be 100%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, nanswers, "Student should have 10 attempts.")
        self.assertTrue(elog.complete, "Student should have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, nanswers, "Student should have 10 attempts for completion.")


@unittest.skipIf("medium" in settings.TESTS_TO_SKIP, "Skipping medium-length test")
class LoadExerciseTest(KALiteDistributedWithFacilityBrowserTestCase):
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


class MainEmptyFormSubmitCaseTest(KALiteDistributedWithFacilityBrowserTestCase):
    """
    Submit forms with no values, make sure there are no errors.

    Note: these are functions on securesync, but
    """

    def test_login_form(self):
        self.empty_form_test(url=self.reverse("login"), submission_element_id="id_username")

    def test_add_student_form(self):
        self.empty_form_test(url=self.reverse("add_facility_student"), submission_element_id="id_username")

    def test_add_teacher_form(self):
        self.empty_form_test(url=self.reverse("add_facility_teacher"), submission_element_id="id_username")

    def test_add_group_form(self):
        self.browser_login_admin()
        self.empty_form_test(url=self.reverse("add_group"), submission_element_id="id_name")
