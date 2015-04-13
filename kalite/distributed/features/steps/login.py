from behave import *
from selenium.common.exceptions import NoSuchElementException

from django.core.urlresolvers import reverse

from kalite.testing.behave_helpers import *

from kalite.facility.models import Facility

from kalite.testing.mixins.facility_mixins import CreateFacilityMixin

TIMEOUT = 3

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

@given("that I am on the homepage")
def step_impl(context):
    go_to_homepage(context)

def go_to_homepage(context):
    url = reverse("homepage")
    context.browser.get(build_url(context, url))

@when("I click log in")
def step_impl(context):
    nav_login = find_id_with_wait(context, "nav_login")
    click_and_wait_for_id_to_appear(context, nav_login, "id_username-container")


@then("there should be no facility drop down")
def step_impl(context):
    try:
        assert not find_id_with_wait(context, "id_facility-container")
    except NoSuchElementException:
        assert True

@then("there should be a facility drop down")
def step_impl(context):
    assert find_id_with_wait(context, "id_facility-container")

@given(u'that I have an account')
def impl(context):
    assert False

@when(u'I enter my password incorrectly')
def impl(context):
    assert False

@then(u'the password should be highlighted')
def impl(context):
    assert False

@then(u'the username should be highlighted')
def impl(context):
    assert False

@then(u'a tooltip should appear on the password box only')
def impl(context):
    assert False

@when(u'I enter my password correctly')
def impl(context):
    assert False

@when(u'I enter my username wrong')
def impl(context):
    assert False

@when(u'I enter my username')
def impl(context):
    assert False

@then(u'a tooltip should appear on the username box only')
def impl(context):
    assert False
