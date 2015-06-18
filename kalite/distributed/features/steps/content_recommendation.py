import random
import datetime

from behave import *
from kalite.testing.behave_helpers import *

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.topic_tools import get_exercise_cache, get_content_cache

@then(u'the resume card should be shown on the very left of the page')
def impl(context):
    assert find_id_with_wait(context, "resume"), "Resume card not displayed!"

@given(u'I have already made some progress on lessons')
def impl(context):
    user = FacilityUser.objects.get(username=context.user, facility=getattr(context, "facility", None))
    exercises = random.sample(get_exercise_cache().keys(), 2)
    for exercise in exercises:
        log, created = ExerciseLog.objects.get_or_create(
            exercise_id=exercise,
            user=user,
            streak_progress=50,
            attempts=15,
            latest_activity_timestamp=datetime.datetime.now()
            )
    context.exercises = exercises
    videos = random.sample(get_content_cache().keys(), 2)
    for video in videos:
        log, created = VideoLog.objects.get_or_create(
            youtube_id=video,
            video_id=video,
            user=user,
            total_seconds_watched=100,
            points=600,
            latest_activity_timestamp=datetime.datetime.now()
            )
    context.videos = videos

@then(u'the explore card should be shown on the very right of the page')
def impl(context):
    assert find_id_with_wait(context, "explore"), "Explore card not displayed!"

@then(u'the next steps card should be shown in the middle of the page')
def impl(context):
    assert find_id_with_wait(context, "nextsteps"), "Next Steps card not displayed!"

@then(u'the last in-progress video/exercise should be shown')
def impl(context):
    assert get_content_cache().get(context.videos[1]).get("path") in context.browser.current_url, "Last in progress video not in %s" % context.browser.current_url

@when(u'I click on the right of an exercise suggestion on the next steps card')
def impl(context):
    card = find_id_with_wait(context, "nextsteps")
    element = card.find_elements_by_tag_name("a")[1]
    click_and_wait_for_page_load(context, element)

@then(u'I should be taken to that topic')
def impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

@when(u'I click in the middle of an exercise suggestion on the next steps card')
def impl(context):
    card = find_id_with_wait(context, "nextsteps")
    element = card.find_elements_by_tag_name("a")[0]
    click_and_wait_for_page_load(context, element)

@then(u'the content recommendation cards should be shown')
def impl(context):
    assert find_id_with_wait(context, "content-rec-wrapper"), "Content Recommendation cards not displayed!"

@when(u'the home page is loaded')
def impl(context):
    go_to_homepage(context)

@when(u'I click on a suggested topic on the explore card')
def impl(context):
    card = find_id_with_wait(context, "explore")
    element = card.find_element_by_tag_name("a")
    click_and_wait_for_page_load(context, element)

@then(u'I should be taken to that exercise')
def impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

@when(u'I click on the resume card lesson')
def impl(context):
    card = find_id_with_wait(context, "resume")
    element = card.find_element_by_tag_name("a")
    click_and_wait_for_page_load(context, element)
