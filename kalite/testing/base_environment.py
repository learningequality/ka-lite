"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.

It simply starts an instn
"""
from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
from urlparse import urljoin

def before_all(context):
    browser = context.browser = webdriver.Firefox()

def after_all(context):
    try:
        context.browser.quit()
    except CannotSendRequest:
        pass

def before_feature(context, feature):
    pass

def after_feature(context, feature):
    pass

def before_scenario(context, scenario):
    pass

def after_scenario(context, scenario):
    pass
