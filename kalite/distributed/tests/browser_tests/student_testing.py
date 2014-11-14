"""
These use a web-browser, along selenium, to simulate user actions.
"""
import time
import glob
import os
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from django.conf import settings
logging = settings.LOG
from django.core.urlresolvers import reverse
from django.utils import unittest

from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins import BrowserActionMixins, FacilityMixins
from kalite.student_testing.models import TestLog
from kalite.student_testing.settings import STUDENT_TESTING_DATA_PATH
from kalite.student_testing.utils import set_exam_mode_on


# TODO (rtibbles): After integration into develop,
# this needs to be modified to create a test and test using the test.
# NOTEFROM (aron): the specific test below has been chosen due to all
# of its questions having a textarea for answer entry, which
# test_exercise_mastery assumes.
TEST_ID = 'g3_t4'


class StudentTestTest(BrowserActionMixins, FacilityMixins, KALiteBrowserTestCase):

    """
    Test tests.
    """
    student_username = 'test_student'
    student_password = 'socrates'

    def setUp(self):
        """
        Create a student, log the student in, and go to the test page.
        """
        super(StudentTestTest, self).setUp()
        self.facility_name = "fac"
        self.facility = self.create_facility(name=self.facility_name)
        self.student = self.create_student(username=self.student_username,
                                           password=self.student_password,
                                           facility=self.facility)
        self.browser_login_student(
            self.student_username,
            self.student_password,
            facility_name=self.facility_name,
        )

        set_exam_mode_on(TEST_ID)
        self.browse_to(
            self.live_server_url +
            reverse("test", kwargs={"test_id": TEST_ID}))
        self.browser_check_django_message(num_messages=0)
        self.browser.find_element_by_id('start-test').click()

    def browser_submit_answers(self, answer):
        WebDriverWait(self.browser, 5).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#solutionarea > input[type=text]")))
        self.browser.find_element_by_id(
            'solutionarea').find_element_by_css_selector(
            'input[type=text]').click()
        self.browser_send_keys(unicode(answer))
        self.browser_send_keys(Keys.RETURN)
        self.browser_check_django_message(num_messages=0)

    @unittest.skipIf(settings.RUNNING_IN_TRAVIS, "I CAN'T TAKE THIS ANYMORE!")
    def test_exercise_mastery(self):
        """
        On a test page, give three answers to complete test.
        """
        answer = "notrightatall"

        total_questions = 30    # tester, check the test to determine this

        for i in range(0, 30):
            self.browser_submit_answers(answer)

        # Now test the models
        testlog = TestLog.objects.get(test=TEST_ID, user=self.student)
        self.assertEqual(testlog.index, total_questions, "Index should be %s" % total_questions)
        self.assertTrue(testlog.started, "Student has not started the test.")
        self.assertEqual(
            testlog.total_number,
            total_questions,
            "Student should have %s attempts." % total_questions
        )
        self.assertTrue(
            testlog.complete,
            "Student should have completed the test."
        )
        self.assertEqual(
            testlog.total_correct,
            0,
            "Student should have none correct."
        )


@unittest.skipIf("medium" in settings.TESTS_TO_SKIP, "Skipping medium-length test")
class LoadTestTest(KALiteBrowserTestCase):

    """Tests if the test is loaded without any JS error.

    The test is run over all test urls and check for any JS error.
    Also check that 'started' is registered on starting each test.
    """
    student_username = 'test_student'
    student_password = 'socrates'

    def setUp(self):
        super(LoadTestTest, self).setUp()
        self.student = self.create_student()
        self.browser_login_student(
            self.student_username, self.student_password)

    def test_get_exercise_load_status(self):
        for testfile in glob.iglob(STUDENT_TESTING_DATA_PATH + "/*.json"):
            with open(testfile) as f:
                test_id = os.path.splitext(os.path.basename(f.name))[0]
                set_exam_mode_on(test_id)
                logging.debug("Testing test : " + test_id)
                self.browse_to(
                    self.live_server_url +
                    reverse("test", kwargs={"test_id": test_id}))
                self.browser.find_element_by_id('start-test').click()
                error_list = self.browser.execute_script(
                    "return window.js_errors;")
                if error_list:
                    logging.error(
                        "Found JS error(s) while loading path: " + path)
                    for e in error_list:
                        logging.error(e)
                self.assertFalse(error_list)
                testlog = TestLog.objects.get(test=test_id, user=self.student)
                self.assertTrue(
                    testlog.started, "Student has not started the test.")
                time.sleep(1)
