from behave import *
from kalite.testing.behave_helpers import *


@given("I am on the homepage")
def step_impl(context):
    go_to_homepage(context)
