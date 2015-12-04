from behave import *
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from kalite.testing.behave_helpers import *
from kalite.topic_tools.content_models import update_item

TIMEOUT = 3


@given(u"I open some unavailable content")
def step_impl(context):
    update_item(path="khan/math/early-math/cc-early-math-counting-topic/cc-early-math-counting/counting-with-small-numbers/", update={"available": False})
    context.browser.get(build_url(context, reverse("learn") + "khan/math/early-math/cc-early-math-counting-topic/cc-early-math-counting/counting-with-small-numbers/"))


@given(u"I open some available content")
def step_impl(context):
    update_item(path="khan/math/arithmetic/addition-subtraction/basic_addition/addition_1/", update={"available": True})
    context.browser.get(build_url(context, reverse("learn") + "khan/math/arithmetic/addition-subtraction/basic_addition/addition_1/"))


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
    # Wait for .content, a rule-of-thumb for ajax stuff to finish, and thus for .alerts to appear (if any).
    find_css_class_with_wait(context, "content")
    assert_no_element_by_css_selector(context, ".alert")
