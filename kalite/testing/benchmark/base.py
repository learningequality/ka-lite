""" base class for KA-LITE benchmarks

    Provides a wrapper for benchmarks, specifically to:
    a) accurately record the test conditions/environment
    b) to record the duration of the task
    d) to allow multiple iterations of the task so that
        an average time can be calculated

    Benchmark results are returned in a python dict

    These benchmarks do not use unittest or testrunner frameworks
"""
import platform
import random
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions, ui

from django.conf import settings; logging = settings.LOG


class Common(object):

    def __init__(self, comment=None, fixture=None, **kwargs):

        self.return_dict = {}
        self.return_dict['comment'] = comment
        self.return_dict['class']=type(self).__name__
        self.return_dict['uname'] = platform.uname()
        self.return_dict['fixture'] = fixture
        try:
            self.verbosity = int(kwargs.get("verbosity"))
        except:
            self.verbosity = 1

        try:
            branch = subprocess.Popen(["git", "describe", "--contains", "--all", "HEAD"], stdout=subprocess.PIPE).communicate()[0]
            self.return_dict['branch'] = branch[:-1]
            head = subprocess.Popen(["git", "log", "--pretty=oneline", "--abbrev-commit", "--max-count=1"], stdout=subprocess.PIPE).communicate()[0]
            self.return_dict['head'] = head[:-1]
        except:
            self.return_dict['branch'] = None
            self.return_dict['head'] = None

        # if setup fails, what could we do?
        #   let the exception bubble up is the best.
        try:
            self._setup(**kwargs)
        except Exception as e:
            logging.debug("Failed setup (%s); trying to tear down" % e)
            try:
                self._teardown()
            except:
                pass
            raise e

    def execute(self, iterations=1):

        if iterations < 1: iterations = 1

        if hasattr(self, 'max_iterations'):
            if iterations > self.max_iterations:
                iterations = self.max_iterations

        self.return_dict['iterations'] = iterations
        self.return_dict['individual_elapsed'] = {}
        self.return_dict['post_execute_info'] = {}
        self.return_dict['exceptions'] = {}

        for i in range(iterations):
            self.return_dict['exceptions'][i+1] = []
            start_time = time.time()
            try:
                self._execute()
                self.return_dict['individual_elapsed'][i+1] = time.time() - start_time
            except Exception as e:
                self.return_dict['individual_elapsed'][i+1] = None
                self.return_dict['exceptions'][i+1].append(e)
                logging.error("Exception running execute: %s" % e)

            try:
                self.return_dict['post_execute_info'][i+1] = self._get_post_execute_info()
            except Exception as e:
                self.return_dict['post_execute_info'][i+1] = None
                self.return_dict['exceptions'][i+1].append(e)
                logging.error("Exception getting execute info: %s" % e)



        mean = lambda vals: sum(vals)/float(len(vals)) if len(vals) else None
        self.return_dict['average_elapsed'] = mean([v for v in self.return_dict['individual_elapsed'].values() if v is not None])

        try:
            self._teardown()
        except Exception as e:
            logging.error(e)

        return self.return_dict

    def _setup(self, behavior_profile=None, **kwargs):
        """
        All benchmarks can take a random seed,
        all should clean / recompile
        """
        self.random=random.Random() #thread-safe local instance of random
        if behavior_profile:
            self.behavior_profile = behavior_profile
            self.random.seed(self.behavior_profile)

    def _execute(self): pass
    def _teardown(self): pass
    def _get_post_execute_info(self): pass


class UserCommon(Common):
    def _setup(self, username="s1", password="s1", **kwargs):
        # Note: user must exist
        super(UserCommon, self)._setup(**kwargs)

        self.username = username
        self.password = password


class SeleniumCommon(UserCommon):
    def _setup(self, url="http://localhost:8008/", timeout=30, **kwargs):
        # Note: user must exist
        super(SeleniumCommon, self)._setup(**kwargs)

        self.url = url if not url or url[-1] != "/" else url[:-1]

        self.browser = webdriver.Firefox()
        self.timeout = timeout

        self._do_signup()

    def _teardown(self):
        self.browser.close()

    def _do_signup(self):
        # Go to the webpage
        self.browser.get(self.url)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "logo"]))

        # Log out any existing user
        if self.browser.find_elements_by_id("nav_logout"):
            nav = self.browser.find_element_by_id("nav_logout")
            if nav.is_displayed():
                self.browser.find_element_by_id("nav_logout").click()
                wait = ui.WebDriverWait(self.browser, self.timeout)
                wait.until(expected_conditions.title_contains(("Home")))

        # Go to the sign-up page
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "nav_signup"]))
        self.browser.find_element_by_id("nav_signup").click()
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.title_contains(("Sign up")))

        # Sign up (don't choose facility or group)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "id_username"]))
        self.browser.find_element_by_id("id_username").send_keys(self.username)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "id_password_first"]))
        self.browser.find_element_by_id("id_password_first").send_keys(self.password)
        self.browser.find_element_by_id("id_password_recheck").send_keys(self.password)
        self.browser.find_element_by_id("id_password_recheck").send_keys(Keys.TAB + Keys.RETURN)
        wait = ui.WebDriverWait(self.browser, self.timeout)
        wait.until(expected_conditions.visibility_of_element_located(["id", "logo"]))
