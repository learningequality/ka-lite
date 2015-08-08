"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.
"""
from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connections

from kalite.testing.base import KALiteTestCase
from kalite.testing.behave_helpers import login_as_admin, login_as_coach, logout, login_as_learner

def before_all(context):
    pass

def after_all(context):
    pass

def before_feature(context, feature):
    pass

def after_feature(context, feature):
    pass

# FYI: scenario tags are inherited from features, so tagging a feature is almost the same as tagging each
# scenario individually, as long as you are cautious not to duplicate logic in before_feature and before_scenario.
def before_scenario(context, scenario):
    database_setup(context)

    browser = context.browser = webdriver.Firefox()
    # ensure the window is reasonably sized.
    browser.set_window_size(2560, 1920)

    context.logged_in = False
    # A superuser now needs to exist or UI is blocked by a modal.
    # https://github.com/learningequality/ka-lite/pull/3668
    if not User.objects.filter(is_superuser=True).exists():
        assert User.objects.create_superuser(
            username='superusername',
            password='superpassword',
            email='super@email.com'
        ), "Didn't create an admin user"
    if "as_admin" in context.tags:
        context.logged_in = True
        login_as_admin(context)
    elif "as_coach" in context.tags:
        context.logged_in = True
        login_as_coach(context)
    elif "as_learner" in context.tags:
        context.logged_in = True
        login_as_learner(context)

def after_scenario(context, scenario):
    if context.logged_in:
        logout(context)
    try:
        context.browser.quit()
    except CannotSendRequest:
        pass

    database_teardown(context)

def database_setup(context):
    """
    Behave features are analogous to test suites, and behave scenarios are analogous to TestCases, but due to
    implementation details each _feature_ is wrapped in a TestCase. This and database_teardown should simulate the
    setup/teardown done by TestCases in order to achieve consistent isolation.
    """
    KALiteTestCase.setUpDatabase()

def database_teardown(context):
    """
    Behave features are analogous to test suites, and behave scenarios are analogous to TestCases, but due to
    implementation details each _feature_ is wrapped in a TestCase. This and database_setup should simulate the
    setup/teardown done by TestCases in order to achieve consistent isolation.
    """
    for alias in connections:
        call_command("flush", database=alias, interactive=False)
