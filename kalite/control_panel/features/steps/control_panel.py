from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *
from kalite.facility.models import Facility


@given("There are no facilities")
def step_impl(context):
    if Facility.objects.count() != 0:
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
    click_and_wait_for_page_load(context, create_facility_link)
    submit_facility_form(context)


@then("I should see a facility in the table")
def step_impl(context):
    table = find_id_with_wait(context, "facilities-table")
    table_row = table.find_element_by_tag_name("tr")
    assert table_row is not None


def go_to_facilities_page(context):
    url = reverse("zone_redirect")
    context.browser.get(build_url(context, url))


def submit_facility_form(context):
    """ Just do the minimum to submit the facility form. """
    facility_form = find_id_with_wait(context, "facility_form")
    name_field = find_id_with_wait(context, "id_name")
    name_field.send_keys("The Fortress of Solitude")
    facility_form.submit()


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
