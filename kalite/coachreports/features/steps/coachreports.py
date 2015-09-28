import datetime
import random

from behave import *
from kalite.testing.behave_helpers import *
from django.core.urlresolvers import reverse

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from kalite.facility.models import FacilityGroup

from kalite.main.models import ExerciseLog, AttemptLog

from kalite.testing.mixins.facility_mixins import CreateStudentMixin, CreateGroupMixin

from kalite.topic_tools.content_models import get_random_content
from securesync.models import Device

colour_legend = {
    "light blue": "#C0E7F3",
    "dark green": "#5AA685",
    "red": "#FD795B",
    "grey": "#EEEEEE",
}

@given("I am on the coach report")
def step_impl(context):
    url = reverse("coach_reports", kwargs={"zone_id": getattr(Device.get_own_device().get_zone(), "id", "None")})
    context.browser.get(build_url(context, url))
    # TODO(benjaoming) : This takes an awful lot of time to load the first
    # time it's built because of /api/coachreports/summary/?facility_id
    # being super slow
    try:
        find_id_with_wait(context, "summary_mainview", wait_time=60)
    except TimeoutException:
        raise RuntimeError("Could not find element, this was the DOM:\n\n" + context.browser.execute_script("return document.documentElement.outerHTML"))

@given("there is no data")
def step_impl(context):
    if FacilityUser.objects.count() != 0:
        for f in FacilityUser.objects.all():
            f.soft_delete()

@then("I should see a warning")
def step_impl(context):
    warning = find_css_class_with_wait(context, "alert-warning")
    assert warning, "No warning shown."

@then(u"there should be no Show Tabular Report button")
def impl(context):
    assert_no_element_by_css_selector(context, "#show_tabular_report")

@then(u"I should be taken to the learner's progress report page")
def impl(context):
    assert reverse("student_view") in context.browser.current_url, "Assertion failed. {url} not in {current_url}".format(url=reverse("student_view"), current_url=context.browser.current_url)

@given(u"I am on the detail panel")
def impl(context):
    context.execute_steps(u"""
        Given I am on the tabular report
        When I click on the partial colored cell
        Then I should see the detail panel emerge from beneath the row
        """)

@then(u"there should be three learner rows displayed")
def impl(context):
    # Wait for appearance
    find_css_class_with_wait(context, "user-data-row")
    # Find all the rows
    rows = context.browser.find_elements_by_css_selector(".user-data-row")
    assert len(rows) == 3, "Incorrect number of user rows in tabular report"

@when(u"I select the preferred group")
def impl(context):
    dropdown = Select(find_id_with_wait(context, "group-select"))
    dropdown.select_by_visible_text("0")
    # For some reason this only triggers properly if you defocus or press enter after the select
    dropdown = find_id_with_wait(context, "group-select")
    dropdown.send_keys(Keys.RETURN)

@given(u"I am on the tabular report")
def impl(context):
    create_some_learner_data()
    context.execute_steps(u"""
        Given I am on the coach report
        When I click on the Show Tabular Report button
        Then I should see the tabular report
        """)

def create_some_learner_data():
    """
    Just create a lil' bit-o-data of each type, to populate the table.
    """
    user = CreateStudentMixin.create_student()
    attempt_states = (  # (name, streak_progress, attempt_count)
        ("not started", 0, 0),
        ("completed", 100, 15),
        ("attempted", 50, 10),
        ("struggling", 30, 25),
    )
    exercises = get_random_content(kinds=["Exercise"], limit=len(attempt_states))  # Important they are *distinct*
    for state in attempt_states:
        exercise = exercises.pop()
        log, created = ExerciseLog.objects.get_or_create(exercise_id=exercise.get("id"), user=user)
        if "not started" != state[0]:
            log.streak_progress, log.attempts = state[1:]
            for i in range(0, log.attempts):
                AttemptLog.objects.get_or_create(
                    exercise_id=exercise.get("id"),
                    user=user,
                    seed=i,
                    timestamp=datetime.datetime.now()
                )
            log.latest_activity_timestamp = datetime.datetime.now()
            log.save()

@given(u"there are three learners")
def impl(context):
    for f in FacilityUser.objects.all():
        f.soft_delete()
    name = 0
    while FacilityUser.objects.count() < 3:
        context.facility = CreateStudentMixin.create_student(username=str(name))
        name += 1

@given(u'the "{learner}" "{progress_verbs}" an "{exercise}"')
def impl(context, learner, progress_verbs, exercise):
    user = CreateStudentMixin.create_student(username=learner)
    if not progress_verbs == "not started":
        log, created = ExerciseLog.objects.get_or_create(exercise_id=exercise, user=user)
        if progress_verbs == "completed":
            log.streak_progress = 100
            log.attempts = 15
        elif progress_verbs == "attempted":
            log.streak_progress = 50
            log.attempts = 10
        elif progress_verbs == "struggling":
            log.streak_progress = 30
            log.attempts = 25
        for i in range(0, log.attempts):
            attempt_log, created = AttemptLog.objects.get_or_create(exercise_id=exercise, user=user, seed=i, timestamp=datetime.datetime.now())
        log.latest_activity_timestamp = datetime.datetime.now()
        log.save()

@then(u'I should see the "{exercise}" marked for "{learner}" as "{progress_text}" and coloured "{progress_colour}"')
def impl(context, exercise, learner, progress_text, progress_colour):
    if progress_text == u"None":
        progress_text = u""

    user = FacilityUser.objects.get(username=learner)
    data_row = find_id_with_wait(context, user.id)
    cell = data_row.find_element_by_css_selector("td[value={exercise}]".format(exercise=exercise))
    assert cell.text == progress_text, "Progress text for {learner}, on {exercise} incorrect".format(learner=learner, exercise=exercise)
    assert rgba_to_hex(cell.value_of_css_property("background-color")) == colour_legend[progress_colour]

@when(u"I click on the learner name")
def impl(context):
    student_name = find_css_class_with_wait(context, "student-name")
    click_and_wait_for_page_load(context, student_name)

@then(u"I should be taken to that exercise within the Learn tab")
def impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

@then(u"I should see the contents of the detail panel change according to the completed cell")
def impl(context):
    pagination_wrapper = find_css_class_with_wait(context, "pagination")
    # Navigation for the completed cell should contain 6 options, ceil(15/4) + 2 for prev/next
    assert len(pagination_wrapper.find_elements_by_tag_name("li")) == 6

@when(u"I click on the Show Tabular Report button")
def impl(context):
    # TODO(benjaoming): For whatever reason, we have to wait an awful lot
    # of time for this to show up because
    # /api/coachreports/summary/?facility_id=XXX is super slow
    try:
        find_id_with_wait(context, "show_tabular_report", wait_time=30).click()
    except TimeoutException:
        raise RuntimeError("Could not find element, this was the DOM:\n\n" + context.browser.execute_script("return document.documentElement.outerHTML"))

@then(u"I should not see the tabular report anymore")
def impl(context):
    assert_no_element_by_css_selector(context, "#displaygrid")

@then(u"I should see the detail panel emerge from beneath the row")
def impl(context):
    assert find_id_with_wait(context, "displaygrid")

@when(u"I click on the Hide Tabular Report button")
def impl(context):
    # TODO(benjaoming): For whatever reason, we have to wait an awful lot
    # of time for this to show up because
    # /api/coachreports/summary/?facility_id=XXX is super slow
    find_clickable_id_with_wait(context, "show_tabular_report", wait_time=30).click()

@then(u"I should see the list of two groups that I teach")
def impl(context):
    dropdown = Select(find_id_with_wait(context, "group-select"))
    assert len(dropdown.options) == 4, "Only {n} displayed".format(n=len(dropdown.options))

@then(u"there should be ten exercise columns displayed")
def impl(context):
    find_css_class_with_wait(context, "headrow")
    assert len(context.browser.find_elements_by_css_selector(".headrow.data")) == 10, len(context.browser.find_elements_by_css_selector(".headrow.data"))

@when(u"I click on the dropdown button under the Group label")
def impl(context):
    find_id_with_wait(context, "group-select").click()

@when(u"I click on the exercise name")
def impl(context):
    headrow = find_css_class_with_wait(context, "headrow")
    click_and_wait_for_page_load(context, headrow.find_element_by_tag_name("a"))

@given(u"all learners have completed ten exercises")
def impl(context):
    exercises = get_random_content(kinds=["Exercise"], limit=10)
    for user in FacilityUser.objects.all():
        for exercise in exercises:
            log, created = ExerciseLog.objects.get_or_create(
                exercise_id=exercise.get("id"),
                user=user,
                streak_progress=100,
                attempts=15,
                latest_activity_timestamp=datetime.datetime.now()
                )


@given(u"there are two groups")
def impl(context):
    for f in FacilityGroup.objects.all():
        f.soft_delete()
    name = 0
    while FacilityGroup.objects.count() < 2:
        context.facility = CreateGroupMixin.create_group(name=str(name))
        name += 1

@then(u"I should see the option of selecting all groups")
def impl(context):
    dropdown = Select(find_id_with_wait(context, "group-select"))
    assert dropdown.options[0].text == "All"

@then(u"I should not see the detail panel anymore")
def impl(context):
    assert_no_element_by_css_selector(context, "#details-panel-view")

@when(u"I click on the partial colored cell")
def impl(context):
    click_and_wait_for_id_to_appear(context, find_css_with_wait(context, "td.partial"), "details-panel-view",
                                    wait_time=30)

@then(u"I should see a Hide Tabular Report button")
def impl(context):
    # TODO(benjaoming): For whatever reason, we have to wait an awful lot
    # of time for this to show up because
    # /api/coachreports/summary/?facility_id=XXX is super slow
    tab_button = find_clickable_id_with_wait(context, "show_tabular_report", wait_time=30)
    assert tab_button.text == "Hide Tabular Report"

@then(u"I should see the tabular report")
def impl(context):
    assert find_id_with_wait(context, "displaygrid")

@then(u"I should see the contents of the summary change according to the group selected")
def impl(context):
    dropdown = Select(find_id_with_wait(context, "group-select"))
    group_text = dropdown.first_selected_option.text
    assert group_text in find_css_class_with_wait(context, "status_name").text

@when(u"I click on the completed colored cell")
def impl(context):
    click_and_wait_for_id_to_appear(context, find_css_with_wait(context, "td.complete"), "details-panel-view")
