from behave import *
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from kalite.testing.behave_helpers import *

TIMEOUT = 3

@given("I open some content")
def step_impl(context):
    context.browser.get(build_url(context, reverse("learn") + "khan/math/algebra/introduction-to-algebra/overview_hist_alg/origins-of-algebra/"))

@given("the content is not available")
def step_impl(context):
    # Currently no content is available - we get this for free!
    pass

@then("I should see an alert")
def step_impl(context):
    # This wait time needs to be very long for now, as it may involve loading the topic tree data.
    assert alert_in_page(context.browser, wait_time=120), "No alert found!"

@then("the alert should tell me the content is not available")
def step_impl(context):
    message = "This content was not found! You must login as an admin/coach to download the content."
    assert message in alert_in_page(context.browser).text, "Message not found!"
