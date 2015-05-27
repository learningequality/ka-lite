from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

from kalite.facility.models import Facility

from kalite.testing.mixins.facility_mixins import CreateFacilityMixin, CreateStudentMixin

PAGE_RELOAD_TIMEOUT = 10

@given("there is one facility")
def step_impl(context):
    if Facility.objects.count() != 0:
        for f in Facility.objects.all():
            f.soft_delete()
    context.facility = CreateFacilityMixin.create_facility()

@given("there is more than one facility")
def step_impl(context):
    name = 0
    while Facility.objects.count() < 2:
        context.facility = CreateFacilityMixin.create_facility(name=str(name))
        name += 1

@when("I click log in")
def step_impl(context):
    nav_login = find_id_with_wait(context, "nav_login")
    click_and_wait_for_id_to_appear(context, nav_login, "id_username-container")


@then("there should be no facility drop down")
def step_impl(context):
    assert not find_id_with_wait(context, "id_facility-container")

@then("there should be a facility drop down")
def step_impl(context):
    assert find_id_with_wait(context, "id_facility-container")

@given('I have an account')
def impl(context):
    context.user = CreateStudentMixin.create_student()
    context.password = CreateStudentMixin.DEFAULTS["password"]

@when('I enter my password incorrectly')
def impl(context):
    fill_password(context, "notarealpasswordIpromise")

@when('I enter my password correctly')
def impl(context):
    fill_password(context, context.password)

@when('I enter my username incorrectly')
def impl(context):
    fill_username(context, "notarealusernameIswear")

@when('I enter my username correctly')
def impl(context):
    fill_username(context, context.user.username)

@when('I click the login button')
def impl(context):
    login_button = find_css_class_with_wait(context, "login-btn")
    # Grab an element reference from the current page. Used to test a page reload later.
    context.wait_elem = context.browser.find_element_by_tag_name("body")
    login_button.click()

@then('a tooltip should appear on the username box only')
def impl(context):
    assert check_single_popover(context, "username")

@then('the password should be highlighted')
def impl(context):
    check_highlight(context, "password")

@then('the username should be highlighted')
def impl(context):
    check_highlight(context, "username")

@then('a tooltip should appear on the password box only')
def impl(context):
    assert check_single_popover(context, "password")

@then('the page should reload')
def impl(context):
    assert WebDriverWait(context.browser, PAGE_RELOAD_TIMEOUT).until(
        EC.staleness_of(context.wait_elem)
    )

def fill_field(context, text, field_id):
    field = find_id_with_wait(context, field_id)
    field.send_keys(text)

def fill_username(context, text):
    fill_field(context, text, "id_username")

def fill_password(context, text):
    fill_field(context, text, "id_password")

def check_highlight(context, item):
    highlight = find_css_class_with_wait(context, "has-error")
    actual = highlight.get_attribute("id")
    expected = "id_{item}-container".format(item=item)
    assert expected == actual, "Expected id: {exp}\n Actual id: {act}".format(exp=expected,act=actual)

def check_single_popover(context, item):
    popover = find_id_with_wait(context, "id_{item}-popover".format(item=item))
    return (len(context.browser.find_elements_by_class_name("popover")) == 1) and "popover" in popover.get_attribute("class")