"""
These methods will probably be used again and again in behave tests.
We'll make a few assumptions: every function here takes a behave context
as the first positional argument, and should assert what it expects from 
that context in order to function (instead of just silently failing).
"""
import httplib
import json

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urlparse import urljoin

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

# Use these for now, so that we don't DROurselves, but eventually
# we'll want to move away from mixins.
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.testing.mixins.django_mixins import CreateAdminMixin


# Maximum time to wait when trying to find elements
MAX_WAIT_TIME = 1


def find_css_class_with_wait(context, css_class, **kwargs):
    """ Tries to find an element with given css class with an explicit timeout.
    context: a behave context
    css_class: A string with the css class (no leading .)
    kwargs: can optionally pass "wait_time", which will be the max wait time in
        seconds. Default is defined by behave_helpers.py
    Returns the element if found or None
    """
    return _find_elem_with_wait(context, (By.CLASS_NAME, css_class), **kwargs)


def _find_elem_with_wait(context, by, wait_time=MAX_WAIT_TIME):
    """ Tries to find an element with an explicit timeout.
    "Private" function to hide Selenium details.
    context: a behave context
    by: A tuple selector used by Selenium
    wait_time: The max time to wait in seconds
    Returns the element if found or None
    """
    try:
        return WebDriverWait(context.browser, wait_time).until(
            EC.presence_of_element_located(by)
        )
    except TimeoutException:
        return None


def build_url(context, url):
    return urljoin(context.config.server_url, url)


def login_as_admin(context, admin_name="admin", admin_pass="abc123"):
    # Create the user if it doesn't exist
    if not User.objects.filter(username=admin_name):
      # TODO(MCGallaspy): Get rid of old integration tests and refactor the mixin methods
      # as functions here.
      class ContextWithMixin(CreateAdminMixin):
          def __init__(self):
              self.browser = context.browser
      context_wm = ContextWithMixin()
      context_wm.create_admin(username=admin_name, password=admin_pass)
    data = json.dumps({"username": admin_name, "password": admin_pass})
    url = reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "login/"
    post(context, url, data)


def logout(context):
    url = reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "logout/"
    get(context, url)


def post(context, url, data=""):
    """ Sends a POST request to the testing server associated with context
    
    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    data: A string containing the body of the request

    Returns the response.
    """
    return request(context, url, method="POST", data=data)


def get(context, url, data=""):
    """ Sends a GET request to the testing server associated with context
    
    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    data: A string containing the body of the request

    Returns the response.
    """
    return request(context, url, method="GET", data=data)


def request(context, url, method="GET", data=""):
    """ Make a request to the testing server associated with context

    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    method: The HTTP method to use, i.e. GET, POST
    data: A string containing the serialized JSON body of the request

    Returns the response.
    """

    # A way to gain access to mixins, so that essential code is not duplicated
    # Be careful how you use this!
    # TODO(MCGallaspy): Get rid of old integration tests and refactor the mixin methods
    # as functions here.
    class ContextWithMixin(BrowserActionMixins):
        def __init__(self):
            self.browser = context.browser
    
    context_wm = ContextWithMixin()
  
    context.browser.get(build_url(context, reverse("homepage")))
    context_wm.browser_wait_for_js_object_exists("$") 
    context.browser.execute_script('window.FLAG=false; $.ajax({type: "%s", url: "%s", data: \'%s\', contentType: "application/json", success: function(data){window.FLAG=true; window.DATA=data}})' % (method, url, data))
    context_wm.browser_wait_for_js_condition("window.FLAG")
    resp = context.browser.execute_script("return window.DATA")

    return resp
