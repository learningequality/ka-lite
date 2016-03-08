import datetime
import random

from behave import *
from kalite.testing.behave_helpers import *
from django.core.urlresolvers import reverse

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from kalite.facility.models import FacilityGroup

from kalite.testing.mixins.facility_mixins import FacilityMixins

@given("there is a facility")
def step_impl(context):
    context.facility = FacilityMixins.create_facility()

@given("I am on the signup page")
def step_impl(context):
    context.facility = FacilityMixins.create_facility()
    signup_url = "%s%s%s" % (reverse('facility_user_signup'), "?&facility=", context.facility.id)
    context.browser.get(build_url(context, signup_url))

@given("there are no groups")
def step_impl(context):
    if FacilityGroup.objects.count() != 0:
        for f in FacilityGroup.objects.all():
            f.soft_delete()

@given("there is a group")
def step_impl(context):
    context.group = FacilityMixins.create_group(facility=context.facility)

@then("the group selector should be hidden")
def step_impl(context):
    assert_no_element_by_xpath_selector(context, "//label[@for='id_group']")

@then("the group selector should be shown")
def step_impl(context):
    group_label = context.browser.find_element_by_xpath("//label[@for='id_group']")
    assert group_label.is_displayed()