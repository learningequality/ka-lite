from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

TIMEOUT = 3

@when("I search for 'Math'")
def step_impl(context):
    search_for(context, "Math")

@when("I search for something")
def step_impl(context):
    search_for(context, "Basic Addition")

@when("I click on the first option")
def step_impl(context):
    menu_item = find_css_class_with_wait(context, "ui-menu-item")
    assert menu_item, "No menu item on page."
    click_and_wait_for_page_load(context, menu_item)

@then("I should see a list of options")
def step_impl(context):
    auto_complete_list = find_css_class_with_wait(context, "ui-menu-item")
    assert auto_complete_list, "Auto complete list not found on page."

@then("I should navigate to a content page")
def step_impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

def search_for(context, text):
    search_field = find_id_with_wait(context, "search")
    search_field.send_keys(text)