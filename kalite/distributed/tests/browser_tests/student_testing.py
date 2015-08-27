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
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.facility_mixins import FacilityMixins
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
