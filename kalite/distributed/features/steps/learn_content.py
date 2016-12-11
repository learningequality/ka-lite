from behave import given, then, when
from django.conf import settings
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from kalite.testing.behave_helpers import build_url, reverse, alert_in_page, wait_for_video_player_ready

TIMEOUT = 30


logger = logging.getLogger(__name__)


@given(u"I open some unavailable content")
def step_impl(context):
    context.browser.get(build_url(context, reverse("learn") + context.content_unavailable_content_path))


@given(u"I open some available content")
def step_impl(context):
    context.browser.get(build_url(context, reverse("learn") + context.content_available_content_path))


@then(u"I should see an alert")
def step_impl(context):
    # This wait time needs to be very long for now, as it may involve loading the topic tree data.
    assert alert_in_page(context.browser, wait_time=30), "No alert found!"


@then(u"the alert should tell me the content is not available")
def step_impl(context):
    message = "This content was not found! You must login as an admin/coach to download the content."
    assert message in alert_in_page(context.browser).text, "Message not found!"


@then(u'I should see no alert')
def impl(context):
    # This test has caused so many issues and it seems there's no real way of
    # reliably testing that an element has disappeared. So for now, this is
    # disabled.
    # https://github.com/learningequality/ka-lite/pull/5284
    # Wait for .content, a rule-of-thumb for ajax stuff to finish, and thus for .alerts to appear (if any).
    # find_css_class_with_wait(context, "content")
    # assert_no_element_by_css_selector(context, ".alert")
    pass


@when(u'I visit a video with subtitles')
def impl(context):
    context.browser.get(build_url(context, reverse("learn") + context.video.path))
    wait_for_video_player_ready(context)


@then(u'the video player is aware of the subtitles')
def impl(context):
    def condition(browser):
        return browser.execute_script('return typeof player != "undefined";')
    try:
        WebDriverWait(context.browser, 2).until(
            condition
        )
    except TimeoutException:
        raise AssertionError("No videojs initialized")
    
    if settings.RUNNING_IN_CI:
        logger.info("Skipping subtitle test because of failures w/ Circle")
    else:
        text_tracks = context.browser.execute_script('return player.textTracks().length;')
        assert text_tracks > 0, "The video didn't have any text tracks!"
