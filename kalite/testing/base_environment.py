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
from django.contrib.auth.models import User

from kalite.testing.behave_helpers import login_as_admin, login_as_coach, logout, login_as_learner

def before_all(context):
    pass

def after_all(context):
    pass

def before_feature(context, feature):
    browser = context.browser = webdriver.Firefox()
    # ensure the window is reasonably sized.
    browser.set_window_size(2560, 1920)

    context.logged_in = False
    # A superuser now needs to exist or UI is blocked by a modal.
    # https://github.com/learningequality/ka-lite/pull/3668
    if not User.objects.exists():
        User.objects.create_superuser(username='superusername', password='superpassword', email='super@email.com')
    if "as_admin" in feature.tags:
        context.logged_in = True
        login_as_admin(context)
    elif "as_coach" in feature.tags:
        context.logged_in = True
        login_as_coach(context)
    elif "as_learner" in feature.tags:
        context.logged_in = True
        login_as_learner(context)

def after_feature(context, feature):
    if context.logged_in:
        logout(context)
    try:
        context.browser.quit()
    except CannotSendRequest:
        pass

def before_scenario(context, scenario):
    pass

def after_scenario(context, scenario):
    pass
