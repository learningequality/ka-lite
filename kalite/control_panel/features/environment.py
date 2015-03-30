"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.
It sets up a test server and test database by using the LiveServerTestCase
machinery.
"""
from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
from urlparse import urljoin

from django.test.testcases import LiveServerTestCase

from kalite.testing.behave_helpers import login_as_admin, logout

def before_all(context):
    pass

def after_all(context):
    pass

def before_feature(context, feature):
    context.logged_in = False
    if "as_admin" in feature.tags:
        context.logged_in = True
        login_as_admin(context)


def after_feature(context, feature):
    if context.logged_in:
        logout(context)


def before_scenario(context, scenario):
    browser = context.browser = webdriver.Firefox()


def after_scenario(context, scenario):
    try:
        context.browser.quit()
    except CannotSendRequest:
        pass
