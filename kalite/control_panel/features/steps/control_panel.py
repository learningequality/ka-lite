from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import build_url, find_css_class_with_wait, find_id_with_wait
from kalite.facility.models import Facility


@given("There are no facilities")
def step_impl(context):
    if Facility.objects.count != 0:
        for f in Facility.objects.all():
            f.soft_delete()


@given("I go to the facilities tab")
def step_impl(context):
    go_to_facilities_page(context)


@then("I should see an empty facilities message")
def step_impl(context):
    elem = get_empty_facilities_msg(context.browser)
    assert elem is not None


@when("I create a facility")
def step_impl(context):
    go_to_facilities_page(context)
    # Wait used because this one is subject to race conditions. 
    create_facility_link = find_css_class_with_wait(context, "create-facility")
    create_facility_link.click()
    submit_facility_form(context)


@then("I should see a facility in the table")
def step_impl(context):
    assert False, "Not yet implemented"


def go_to_facilities_page(context):
    url = reverse("zone_redirect")
    context.browser.get(build_url(context, url))


def submit_facility_form(context):
    """ Just do the minimum to submit the facility form. """
    facility_form = find_id_with_wait(context, "facility_form")
    name_field = facility_form.find_element_by_id("id_name")
    name_field.send_keys("The Fortress of Solitude")
    facility_form.submit()


def get_facilities_table(browser):
    """ Returns a Selenium WebElement if it exists, otherwise None
    browser: An instance of Selenium WebDriver
    """
    try:
        # This isn't a single page JS app, so we don't need to use
        # a timeout... it's either going to be there or not
        elem = browser.find_element_by_id("facilities-table")
        return elem
    except NoSuchElementException:
        return None
        

def get_empty_facilities_msg(browser):
    """ Returns a Selenium WebElement if it exists, otherwise None
    browser: An instance of Selenium WebDriver
    """
    try:
        # This isn't a single page JS app, so we don't need to use
        # a timeout... it's either going to be there or not
        elem = browser.find_element_by_id("no-facilities-message")
        return elem
    except NoSuchElementException:
        return None
