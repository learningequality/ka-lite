from behave import *
from selenium.common.exceptions import NoSuchElementException

from facility.models import Facility


@given("There are no facilities")
def step_impl(context):
    if Facility.objects.count != 0:
        for f in Facility.objects.all():
            f.soft_delete()


@given("I go to the facilities tab")
def step_impl(context):
    context.browser.get(context.browser_url("management/zone/None/"))


@then("I should see an empty facilities message")
def step_impl(context):
    elem = get_empty_facilities_msg(context.browser)
    assert elem is not None


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
        
