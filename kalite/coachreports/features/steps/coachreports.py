from behave import *
from kalite.testing.behave_helpers import *
from django.core.urlresolvers import reverse

from kalite.facility.models import FacilityUser

from kalite.testing.mixins.facility_mixins import CreateStudentMixin

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

@then(u"I should be taken to the learner's progress report page")
def impl(context):
    assert True

@given(u"I am on the detail panel")
def impl(context):
    assert True

@then(u"there should be three learner rows displayed")
def impl(context):
    assert True

@given(u"I selected the preferred group")
def impl(context):
    assert True

@given(u"I am on the tabular report")
def impl(context):
    context.execute_steps("""
        Given I am on the coach report
        And I selected the preferred group
        And there are three learners
        And all learners have completed ten exercises
        When I click on the Show Tabular Report button
        Then I should see the tabular report
        """)

@given(u"there are three learners")
def impl(context):
    for f in FacilityUser.objects.all():
        f.soft_delete()
    name = 0
    while FacilityUser.objects.count() < 3:
        context.facility = CreateStudentMixin.create_student(username=str(name))
        name += 1

@then(u"I should see the exercise marked as one hundred percent and colored green")
def impl(context):
    assert True

@when(u"I click on the learner name")
def impl(context):
    assert True

@then(u"I should be taken to that exercise within the Learn tab")
def impl(context):
    assert True

@then(u"I should see the contents of the detail panel change according to that cell")
def impl(context):
    assert True

@when(u"I click on the Show Tabular Report button")
def impl(context):
    assert True

@then(u"I should not see the tabular report anymore")
def impl(context):
    assert_no_element_by_css_selector(context, "#displaygrid")

@given(u"I don't remember what cell I clicked on")
def impl(context):
    assert True

@then(u"I should see the detail panel emerge from beneath the row")
def impl(context):
    assert True

@when(u"I click on the Hide Tabular Report button")
def impl(context):
    assert True

@then(u"I should see the list of groups that I teach")
def impl(context):
    assert True

@then(u"there should be ten exercise columns displayed")
def impl(context):
    assert True

@when(u"I click on the dropdown button under the Group label")
def impl(context):
    assert True

@when(u"I click on the cell again")
def impl(context):
    assert True

@then(u"I should see the exercise name, number of questions, number of attempts, and actions made")
def impl(context):
    assert True

@when(u"I click on the exercise name")
def impl(context):
    assert True

@then(u"I should see the exercise unmarked and colored gray")
def impl(context):
    assert True

@when(u"I click on a group name")
def impl(context):
    assert True

@given(u"that a learner is struggling on a exercise")
def impl(context):
    assert True

@given(u"all learners have completed ten exercises")
def impl(context):
    assert True

@then(u"I should see the exercise marked with a percentage and colored red")
def impl(context):
    assert True

@given(u"that a learner completed the full exercise")
def impl(context):
    assert True

@then(u"I should see the option of selecting all groups")
def impl(context):
    assert True

@then(u"I should not see the detail panel anymore")
def impl(context):
    assert_no_element_by_css_selector(context, "#detailpanel")

@when(u"I click on a colored cell")
def impl(context):
    assert True

@then(u"I should see a Hide Tabular Report button")
def impl(context):
    assert True

@then(u"I should see the the two groups listed")
def impl(context):
    assert True

@then(u"I should see the tabular report")
def impl(context):
    assert True

@given(u"that a learner is progressing on an exercise")
def impl(context):
    assert True

@given(u"that a learner did not start the exercise")
def impl(context):
    assert True

@when(u"I click on the same colored cell")
def impl(context):
    assert True

@then(u"I should see the contents of the summary change according to the group selected")
def impl(context):
    assert True

@given(u"that the tabular report is displayed")
def impl(context):
    assert True

@when(u"I click on a random colored cell")
def impl(context):
    assert True

@then(u"I should see the exercise marked with a percentage and colored light green")
def impl(context):
    assert True
