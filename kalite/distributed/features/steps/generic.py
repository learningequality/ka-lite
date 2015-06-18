from behave import *
from kalite.testing.behave_helpers import *

@given("I am on the homepage")
def step_impl(context):
    go_to_homepage(context)
    context.homepage_elem_ref = context.browser.find_element_by_tag_name("body")  # Grab a reference so later we can check that we're not on this page