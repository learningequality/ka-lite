from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

TIMEOUT = 3

@given("I am on the homepage")
def step_impl(context):
    pass

@given("I search for Basic Addition")
def step_impl(context):
    pass

@when("I search for 'Math'")
def step_impl(context):
    pass

@when("I search for Basic Addition")
def step_impl(context):
    pass

@then("I should see a list of options")
def step_impl(context):
    pass

@then("I should navigate to Basic Addition")
def step_impl(context):
    pass
