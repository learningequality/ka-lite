from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

TIMEOUT = 3

@given("I am on the homepage")
def step_impl(context):
    go_to_homepage(context)

@when("I search for 'Math'")
def step_impl(context):
    search_for(context, "Math")

@when("I search for Basic Addition")
def step_impl(context):
    search_for(context, "Basic Addition")

@when("I click on the first option")
def step_impl(context):
    create_facility_link = find_css_class_with_wait(context, "ui-menu-item")
    click_and_wait_for_page_load(context, create_facility_link)

@then("I should see a list of options")
def step_impl(context):
    auto_complete_list = find_css_class_with_wait(context, "ui-autocomplete")
    assert auto_complete_list

@then("I should navigate to Basic Addition")
def step_impl(context):
    url = context.browser.getUrl()
    assertEqual(url, "/learn/khan/math/arithmetic/addition-subtraction/basic_addition/basic-addition/")

def search_for(text, context):
    search_field = find_id_with_wait(context, "search")
    search_field.send_keys(text)