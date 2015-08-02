from behave import *
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TIMEOUT = 3


@given("I open an exercise")
def step_impl(context):
    pass


@given("the exercise is available")
def step_impl(context):
    # NOTE(MCGallaspy): We really need a way to interact meaningfully with the learn page...
    # It's hard for me and makes me sad. :(
    # context.browser.get(context.browser_url("learn/some/random/exercise"))
    pass


@given("the exercise is not available")
def step_impl(context):
    # See above. This is hard for me to implement. :(
    pass


@then("I should see an alert")
def step_impl(context):
    pass
    #assert alert_in_page(context.browser), "No alert found!"


@then("I will be happy")
def step_impl(context):
    pass


def alert_in_page(browser):
    # How do I safely reason about single-page JS apps...
    # Is this an appropriate timeout value or not?
    # Can we listen for events in our JS apps to improve testability?
    try:
        elem = WebDriverWait(browser, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert"))
        )
        return True
    except TimeoutException:
        return False
