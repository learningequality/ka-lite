from behave import *
from socket import timeout
from mock import patch
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tastypie.exceptions import NotFound

from kalite.main.api_resources import Content

@given("I open an exercise")
def step_impl(context):
    context.browser.get(context.browser_url("/"))

#@patch.object('kalite.main.api_resources.ContentResource', 'obj_get', side_effect = NotFound())
@given("the exercise is available")
def step_impl(context):
    #context.browser.get(context.browser_url("learn/some/random/exercise"))
    pass

#@patch.object('kalite.main.api_resources.ContentResource', 'obj_get', return_value = Content())
@given("the exercise is not available")
def step_impl(context):
    #context.browser.get(context.browser_url("learn/some/random/exercise"))
    pass

@then("I should see an alert")
def step_impl(context):
    assert alert_in_page(context.browser), "No alert found!"

@then("I will be happy")
def step_impl(context):
    pass


def alert_in_page(browser, msg=""):
    try:
        # It's still hard to reason about single-page JS apps...
        # Is this an appropriate timeout value or not?
        WebDriverWait(browser, 1).until(
            EC.presence_of_element_located((By.CLASS, "alert"))
        )
        return True
    except TimeoutException:
        return False
