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
    #context.browser.get(context.browser_url("learn/some/random/exercise"))
    pass

@given("the exercise is not available")
def step_impl(context):
    # See above. This is hard for me to implement. :(
    pass

@then("I will be happy")
def step_impl(context):
    pass
