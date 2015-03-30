"""
environment.py specific to the this app
"""
from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
from urlparse import urljoin

from django.test.testcases import LiveServerTestCase

def before_all(context):

    # So we get a free test server and test database, with appropriate
    # setup and teardown methods
    # If we really want to test the learn page, we would probably need
    # to judiciously stub out a bunch of methods from topic_tools here
    hijacked_test_case = context.hijacked_test_case = HijackTestCase()
    hijacked_test_case.setUpClass()
     
    def browser_url(url):
        return urljoin(hijacked_test_case.live_server_url, url)
    
    context.browser_url = browser_url


def after_all(context):
    context.hijacked_test_case.tearDownClass()


def before_scenario(context, scenario):
    browser = context.browser = webdriver.Firefox()
    # _pre_setup flushes the databse, so we run it before every scenario
    context.hijacked_test_case._pre_setup()


def after_scenario(context, scenario):
    context.hijacked_test_case._post_teardown()
    try:
        context.browser.quit()
    except CannotSendRequest:
        pass


class HijackTestCase(LiveServerTestCase):

    def runTest(self):
        pass
