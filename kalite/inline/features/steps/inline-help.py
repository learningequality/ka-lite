from behave import *

from django.core.urlresolvers import reverse
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from kalite.testing.behave_helpers import build_url, find_css_class_with_wait, find_id_with_wait,\
    elem_is_invisible_with_wait, go_to_homepage


# Id for the clickable element that starts an intro
STARTING_POINT_ID = "inline-btn"
# Classes for the introjs modal and associated elements
MODAL_CLASS = "introjs-tooltip"
STEP_NUMBER_CLASS = "introjs-helperNumberLayer"
HIGHLIGHTED_CLASS = "introjs-showElement"
NEXT_BUTTON_CLASS = "introjs-nextbutton"
BACK_BUTTON_CLASS = "introjs-prevbutton"
SKIP_BUTTON_CLASS = "introjs-skipbutton"


@given("I'm on the manage page")
def step_impl(context):
    go_to_manage_page(context)


@when("I click the starting point")
def step_impl(context):
    start_intro(context)


@then("I see a modal with step number {expected_num:d}")
def step_impl(context, expected_num):

    def condition(driver):
        number_el = driver.find_element_by_class_name(STEP_NUMBER_CLASS)
        actual_num_text = number_el.text
        return int(actual_num_text) == expected_num if actual_num_text else False

    WebDriverWait(context.browser, 30, ignored_exceptions=NoSuchElementException).until(condition)


@then("an element is highlighted")
def step_impl(context):
    elem = find_css_class_with_wait(context, HIGHLIGHTED_CLASS)
    assert elem is not None, "Couldn't find a highlighted element on the page."
    assert elem.is_displayed(), "The highlighted element exists but is not visible."


@then("the modal has a \"next\" button")
def step_impl(context):
    modal = find_css_class_with_wait(context, MODAL_CLASS)
    assert modal is not None, "Couldn't find an intro modal!"
    context.next_button = next_button = modal.find_element_by_class_name(NEXT_BUTTON_CLASS)
    assert next_button.is_displayed(), "\"Next\" button exists but is not visible."


@when("I click the \"{btn_name}\" button")
def step_impl(context, btn_name):
    if btn_name == "next":
        context.next_button.click()
    elif btn_name == "skip":
        context.skip_button.click()
    elif btn_name == "back":
        context.back_button.click()


@given("I've started the intro")
def step_impl(context):
    """ Start the intro and add some elements to the context. """
    go_to_manage_page(context)
    start_intro(context)
    modal = context.modal = find_css_class_with_wait(context, MODAL_CLASS, wait_time=30)
    context.skip_button = modal.find_element_by_class_name(SKIP_BUTTON_CLASS)
    context.next_button = modal.find_element_by_class_name(NEXT_BUTTON_CLASS)
    context.back_button = modal.find_element_by_class_name(BACK_BUTTON_CLASS)


@then("the modal disappears")
def step_impl(context):
    assert elem_is_invisible_with_wait(context, context.modal, wait_time=60), "The modal should not be visible."


@then("the back button is disabled")
def step_impl(context):
    assert "introjs-disabled" in context.back_button.get_attribute("class")


@given("I'm on a page with no intro")
def step_impl(context):
    go_to_homepage(context)


@then("I should not see the starting point")
def step_impl(context):
    try:
        context.browser.find_element_by_id(STARTING_POINT_ID)
        assert False, "There should not be a starting point element for the intro!"
    except NoSuchElementException:
        pass


def go_to_manage_page(context):
    url = reverse("zone_redirect")
    context.browser.get(build_url(context, url))


def start_intro(context):
    sp_elem = find_id_with_wait(context, STARTING_POINT_ID, wait_time=30) #WebElement
    sp_elem.click()