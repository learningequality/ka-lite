"""
These use a web-browser, along selenium, to simulate user actions.
"""
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotVisibleException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import unittest
from django.test.utils import override_settings
from django.utils.translation import ugettext as _

from fle_utils.general import isnumeric
from kalite.facility.models import FacilityUser, Facility
from kalite.main.models import ExerciseLog
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, CreateAdminMixin, FacilityMixins, CreateFacilityMixin
from kalite.topic_tools import get_node_cache

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
class UserRegistrationCaseTest(BrowserActionMixins, KALiteBrowserTestCase, CreateAdminMixin, CreateFacilityMixin):
    username = "user1"
    password = "password"

    def setUp(self):
        super(UserRegistrationCaseTest, self).setUp();
        self.create_admin()
        self.create_facility()

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

        self.browse_to(self.live_server_url + reverse("learn") + get_node_cache("Exercise")[self.EXERCISE_SLUG]["path"])
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
        ui.WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'solutionarea'))
        )
        self.browser.find_element_by_id('solutionarea').find_element_by_css_selector('input[type=text]').click()
        self.browser_send_keys(unicode(answer))
        self.browser.find_element_by_id('check-answer-button').click()

        try:
            ui.WebDriverWait(self.browser, 10).until(
                expected_conditions.visibility_of_element_located((By.ID, 'next-question-button'))
            )
            correct = self.browser.find_element_by_id('next-question-button').get_attribute("value")=="Correct! Next question..."
        except TimeoutException:
            correct = False
        return correct

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    def test_question_correct_points_are_added(self):
        """
        Answer an exercise correctly
        """
        ui.WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'mord'))
        )
        numbers = self.browser.find_elements_by_css_selector("span[class=mord][style]")
        answer = sum(int(num.text) for num in numbers)
        correct = self.browser_submit_answer(answer)
        self.assertTrue(correct, "answer was incorrect")
        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 100 / self.nanswers, "Streak progress should be 10%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, 1, "Student should have 1 attempt.")
        self.assertFalse(elog.complete, "Student should not have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, None, "Student should not have a value for attempts_before_completion.")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    def test_question_incorrect_false(self):
        """
        Answer an exercise incorrectly.
        """
        ui.WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'mord'))
        )
        correct = self.browser_submit_answer(0)
        self.assertFalse(correct, "answer was correct")

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
        ui.WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.CLASS_NAME, 'mord'))
        )

        self.browser_submit_answer(0)

        answer_button_text = self.browser.find_element_by_id("check-answer-button").get_attribute("value")

        self.assertTrue(answer_button_text == "Check Answer", "Answer button changed on incorrect answer!")

    # @unittest.skipIf(getattr(settings, 'CONFIG_PACKAGE', None), "Fails if settings.CONFIG_PACKAGE is set.")
    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    @override_settings(CONFIG_PACKAGE=None)
    def test_exercise_mastery(self):
        """
        Answer an exercise til mastery
        """
        for ai in range(1, 1 + self.nanswers):
            # Hey future maintainer! The visibility_of_element_located
            # requires that the element be ACTUALLY visible on the screen!
            # so you can't just have the test spawn a teeny-bitty browser to
            # the side while you have the world cup occupying a big part of your
            # screen.
            ui.WebDriverWait(self.browser, 10).until(
                expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'mord'))
            )
            numbers = self.browser.find_elements_by_css_selector("span[class=mord][style]")
            answer = sum(int(num.text) for num in numbers)
            correct = self.browser_submit_answer(answer)
            self.assertTrue(correct, "answer was incorrect")

            self.browser_send_keys(Keys.RETURN)  # move on to next question.

        # Now test the models
        elog = ExerciseLog.objects.get(exercise_id=self.EXERCISE_SLUG, user=self.student)
        self.assertEqual(elog.streak_progress, 100, "Streak progress should be 100%")
        self.assertFalse(elog.struggling, "Student is not struggling.")
        self.assertEqual(elog.attempts, self.nanswers, "Student should have %s attempts. Got %s" % (self.nanswers, elog.attempts))
        self.assertTrue(elog.complete, "Student should have completed the exercise.")
        self.assertEqual(elog.attempts_before_completion, self.nanswers, "Student should have %s attempts for completion." % self.nanswers)


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
        self.create_admin()
        self.student = self.create_student(username=student_username, password=student_password)
        self.browser_login_student(student_username, student_password)
        time.sleep(3)
        self.browse_to(self.reverse("exercise_dashboard"))
        self.browser_check_django_message(message_type="error", contains="Your session has been timed out")
        # Check if user redirects to login page after session timeout.
        self.assertEquals(self.browser.current_url, self.reverse("login") )

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

class WatchingVideoAccumulatesPointsTest(BrowserActionMixins, CreateAdminMixin, KALiteBrowserTestCase, CreateFacilityMixin):
    """
    Addresses issue 2864. Ensure that watching a video accumulates points for a student.
    """

    def setUp(self):
        super(WatchingVideoAccumulatesPointsTest, self).setUp()
        self.browser.set_page_load_timeout(30)
        self.create_admin()
        self.create_facility()
        self.browser_register_user(username="johnduck", password="superpassword")
        self.browser_login_student(username="johnduck", password="superpassword")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Passes locally, fails in Travis - MCGallaspy.")
    def test_watching_video_increases_points(self):
        self.browse_to_random_video()
        points = self.browser_get_points()
        self._play_video()
        updated_points = self.browser_get_points()
        self.assertNotEqual(updated_points, points, "Points were not increased after video seek position was changed")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Passes locally, fails in Travis - MCGallaspy.")
    def test_points_update(self):
        self.browse_to_random_video()
        points = self.browser_get_points()
        video_js_object = "channel_router.control_view.topic_node_view.content_view.currently_shown_view.content_view"
        self.browser_wait_for_js_object_exists(video_js_object)
        self.browser.execute_script(video_js_object + ".set_progress(1);")
        updated_points = self.browser_get_points()
        self.assertNotEqual(updated_points, points, "Points were not increased after video progress was updated")

    def _play_video(self):
        """Video might not be downloaded, so simulate "playing" it by firing off appropriate js events."""
        video_js_object = "channel_router.control_view.topic_node_view.content_view.currently_shown_view.content_view"
        self.browser_wait_for_js_object_exists(video_js_object)
        self.browser.execute_script(video_js_object + ".activate()")
        self.browser.execute_script(video_js_object + ".set_progress(0.5)")
        self.browser.execute_script(video_js_object + ".update_progress()")

class PointsDisplayUpdatesCorrectlyTest(KALiteBrowserTestCase, BrowserActionMixins, CreateAdminMixin, CreateFacilityMixin):
    """
    A regression test for issue 2858. When a user with X points gets Y more points and 
    navigates to a new item, the points display reamins X. Only after a third navigation 
    event are the points updated correctly to X + Y + any other points accumulated in the meantime.
    We need to test two different backbone router events here (under distributed/topics/router.js)
    """

    def setUp(self):
        super(PointsDisplayUpdatesCorrectlyTest, self).setUp()
        self.create_admin()
        self.create_facility()
        self.browser_register_user(username="johnduck", password="superpassword")
        self.browser_login_student(username="johnduck", password="superpassword")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "This is a Schroedinger's Cat test - a superposition of fail/ok whose outcome depends on the observer.")
    def test_points_update_after_backbone_navigation(self):
        """
        Tests a navigation event caught by loading another backbone view.
        """
        self.browse_to_random_video()
        points = self.browser_get_points()
        self._play_video()
        self.browse_to_random_video()
        updated_points = self.browser_get_points()
        self.assertNotEqual(updated_points, points, "Points were not updated after a backbone navigation event.")

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "Passes locally, fails in Travis - MCGallaspy.")
    def test_points_update_after_non_backbone_navigation(self):
        """
        Tests navigation event not triggered by loading another backbone view, e.g.
        refreshing the page.
        """
        self.browse_to_random_video()
        points = self.browser_get_points()
        self._play_video()
        self.browse_to(self.reverse("homepage"))
        updated_points = self.browser_get_points()
        self.assertNotEqual(updated_points, points, "Points were not updated after a non-backbone navigation event.")

    def _play_video(self):
        """The video might not be downloaded, so instead we simulate playing it by changing the points on the log_model."""
        log_model_object = "channel_router.control_view.topic_node_view.content_view.currently_shown_view.content_view.log_model"
        self.browser_wait_for_js_object_exists(log_model_object)
        self.browser.execute_script(log_model_object + ".set(\"points\", 9000);" )
        self.browser.execute_script(log_model_object + ".saveNow();" )

class AdminOnlyTabsNotDisplayedForCoachTest(KALiteBrowserTestCase, BrowserActionMixins, CreateAdminMixin, FacilityMixins):
    """ Addresses issue #2990. """

    def setUp(self):
        super(AdminOnlyTabsNotDisplayedForCoachTest, self).setUp()
        self.create_admin()
        self.create_facility()
        self.create_teacher(username="teacher1", password="password")
        self.browser_login_user(username="teacher1", password="password")

    def test_correct_tabs_are_displayed(self):
        """Tabs with the class admin-only should not be displayed, and tabs
        with the class teacher-only should be displayed
        """
        try:
            admin_only_elements = WebDriverWait(self.browser, 10).until(
                expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, "admin-only"))
            )
        except TimeoutException:
            admin_only_elements = []
        teacher_only_elements = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, "teacher-only"))
        )
        # Make sure nav bar is expanded e.g. in a small screen
        try:
            navbar_expand = self.browser.find_element_by_class_name('navbar-toggle')
            self.browser_activate_element(elem=navbar_expand)
            # Wait for the animation to finish
            WebDriverWait(self.browser, 3).until(
                expected_conditions.visibility_of_element_located((By.CLASS_NAME, "nav"))
            )
        except ElementNotVisibleException:
            # browser_activate_element could throw this, meaning nav bar is already visible
            pass

        for el in admin_only_elements:
            self.assertFalse(el.is_displayed(), "Elements with `admin-only` class should not be displayed!")
        for el in teacher_only_elements:
            self.assertTrue(el.is_displayed(), "Elements with `teacher-only` class should be displayed!")

class AlertsRemovedAfterNavigationTest(BrowserActionMixins, CreateAdminMixin, CreateFacilityMixin, KALiteBrowserTestCase):

    def setUp(self):
        super(AlertsRemovedAfterNavigationTest, self).setUp()
        self.create_admin()
        self.create_facility()
        self.browser_register_user(username="johnduck", password="superpassword")

    def test_login_alert_is_removed(self):
        self.browser_login_student(username="johnduck", password="superpassword")
        try:
            self.assertTrue(WebDriverWait(self.browser, 3).until(
                expected_conditions.presence_of_element_located((By.CSS_SELECTOR,"div.alert-dismissible"))
            ))
        except TimeoutException:
            self.fail("No alert present on page after login.")
        try:
            # The function called by navigation event in the single-page JS app.
            self.browser.execute_script("channel_router.control_view.topic_node_view.content_view.show_view()")
        except WebDriverException as e:
            if e.msg == "view is undefined":
                # Since we're circumventing the normal control flow of the single-page JS app, we expect
                # this JS error, which gets passed along as a WebDriverException
                pass
            else:
                raise
        try:
            self.assertTrue(WebDriverWait(self.browser, 3).until(
                expected_conditions.invisibility_of_element_located((By.CSS_SELECTOR,"div.alert-dismissible"))
            ))
        except TimeoutException:
            self.fail("Alert present on page after navigation event. Expected no alerts.")


class CoachHasLogoutLinkTest(BrowserActionMixins, CreateAdminMixin, FacilityMixins, KALiteBrowserTestCase):
    """
    A regression test for issue 3000. Note the judicious use of waits and expected conditions to account for
    various browser sizes and potential server hiccups.
    """

    def setUp(self):
        super(CoachHasLogoutLinkTest, self).setUp()
        self.create_admin()
        self.create_facility()
        self.create_teacher(username="teacher1", password="password")
        self.browser_login_user(username="teacher1", password="password")
        self.browse_to(self.reverse("homepage"))

    def test_logout_link_visible(self):
        nav_logout = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, "nav_logout"))
        )
        self.assertFalse(nav_logout.is_displayed(), "The dropdown menu logout item must not be displayed yet!")
        # Activate the dropdown menu and see if the logout link is visible.
        dropdown_menu = self.browser.find_element_by_xpath("//*[@id=\"wrapper\"]/div[1]/div/div/div[2]/ul/li[7]/a")
        WebDriverWait(self.browser, 3).until(
            expected_conditions.visibility_of(dropdown_menu)
        )
        self.browser_activate_element(elem=dropdown_menu)
        self.assertTrue(nav_logout.is_displayed(), "The dropdown menu logout item is not displayed!")

    def test_logout_link_visible_small_browser_size(self):
        # Check if browser size is too small and menu is collapsed, for mobile.
        self.browser.set_window_size(640, 480)
        expand_menus_button = self.browser.find_element_by_xpath("//*[@id=\"wrapper\"]/div[1]/div/div/div[1]/button")
        WebDriverWait(self.browser, 3).until(
            expected_conditions.visibility_of(expand_menus_button)
        )
        self.browser_activate_element(elem=expand_menus_button)
        self.test_logout_link_visible()
