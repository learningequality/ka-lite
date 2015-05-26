from behave import *
from kalite.testing.behave_helpers import *
from django.core.urlresolvers import reverse

from kalite.facility.models import FacilityUser

@given("I am on the coach report")
def step_impl(context):
    url = reverse("coach_reports")
    context.browser.get(build_url(context, url))

@given("there is no data")
def step_impl(context):
    if FacilityUser.objects.count() != 0:
        for f in FacilityUser.objects.all():
            f.soft_delete()

@then("I should see a warning")
def step_impl(context):
    # TODO (rtibbles): Migrate from old tests
    assert True