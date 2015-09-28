from behave import *
from kalite.testing.behave_helpers import *

from kalite.topic_tools.content_models import get_content_item

@then(u'the resume card should be shown on the very left of the page')
def impl(context):
    assert find_id_with_wait(context, "resume"), "Resume card not displayed!"

@then(u'the explore card should be shown on the very right of the page')
def impl(context):
    assert find_id_with_wait(context, "explore"), "Explore card not displayed!"

@then(u'the next steps card should be shown in the middle of the page')
def impl(context):
    assert find_id_with_wait(context, "nextsteps"), "Next Steps card not displayed!"

@then(u'the last in-progress video/exercise should be shown')
def impl(context):
    assert get_content_item(content_id=context.videos[1].get("id")).get("path") in context.browser.current_url, "Last in progress video not in %s" % context.browser.current_url

@when(u'I click on the right of an exercise suggestion on the next steps card')
def impl(context):
    element = find_css_class_with_wait(context, "content-nextsteps-topic-link")
    click_and_wait_for_page_load(context, element, wait_time=15)

@then(u'I should be taken to that topic')
def impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

@when(u'I click in the middle of an exercise suggestion on the next steps card')
def impl(context):
    element = find_css_class_with_wait(context, "content-nextsteps-lesson-link")
    click_and_wait_for_page_load(context, element, wait_time=15)

@then(u'the content recommendation cards should be shown')
def impl(context):
    # Note: First load from the content recommendation API endpoint is longer, as a cache item gets built.
    assert find_id_with_wait(context, "content-rec-wrapper", wait_time=15), "Content Recommendation cards not displayed!"

@when(u'the home page is loaded')
def impl(context):
    go_to_homepage(context)

@when(u'I click on a suggested topic on the explore card')
def impl(context):
    element = find_css_class_with_wait(context, "content-explore-topic-link")
    click_and_wait_for_page_load(context, element)

@then(u'I should be taken to that exercise')
def impl(context):
    assert "/learn/" in context.browser.current_url, "Assertion failed. '/learn/' not in %s" % context.browser.current_url

@when(u'I click on the resume card lesson')
def impl(context):
    element = find_css_class_with_wait(context, "content-resume-topic-link")
    click_and_wait_for_page_load(context, element)
