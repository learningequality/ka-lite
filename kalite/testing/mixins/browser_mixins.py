import json
import time
import re
import logging

from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..browser import browse_to, setup_browser, wait_for_page_change
from kalite.topic_tools.content_models import get_random_content
from kalite.facility.models import Facility

from django.contrib.auth.models import User

from random import choice

from kalite.testing.browser import hacks_for_phantomjs

FIND_ELEMENT_TIMEOUT = 3

class KALiteTimeout(Exception):
    pass

class BrowserActionMixins(object):

    # not all act as tab stops, but ...
    HtmlFormElements = ["form", "input", "textarea", "label", "fieldset",
                        "legend", "select", "optgroup", "option", "button",
                        "datalist", "keygen", "output"]

    def create_browser(self, browser_type="Firefox"):
        return setup_browser(browser_type)

    def browse_to(self, *args, **kwargs):
        """
        When testing, we have to make sure that the page has loaded before
        testing the resulting page.

        Three ways to specify the url to browse to:
        1. First positional argument
        2. dest_url keyword argument
        3. reverse lookup of url_name argument.

        """
        if kwargs.get("browser"):
            browser = kwargs.get("browser")
            del kwargs["browser"]
        else:
            browser = self.browser
        if args:
            assert "dest_url" not in kwargs
        elif "dest_url" in kwargs:
            assert "url_name" not in kwargs
        elif "url_name" in kwargs:
            kwargs["dest_url"] = self.reverse(kwargs["url_name"])
            del kwargs["url_name"]
        else:
            raise Exception("Must specify the destination url.")

        browse_to(browser, *args, **kwargs)

    def wait_for_page_change(self, source_url, wait_time=0.1, max_retries=40):
        """
        When testing, we have to make sure that the page has loaded before testing the resulting page.
        """

        return wait_for_page_change(self.browser, source_url, wait_time=wait_time, max_retries=max_retries)

    def browser_activate_element(self, **kwargs):
        """
        Given the identifier to a page element, make it active.
        Currently done by clicking TODO(bcipolli): this won't work for buttons,
        so find another way when that becomes an issue.
        """
        browser = kwargs.get("browser", self.browser)
        elem = kwargs.get("elem")
        id = kwargs.get("id")
        name = kwargs.get("name")
        tag_name = kwargs.get("tag_name")
        css_class = kwargs.get("css_class")
        xpath = kwargs.get("xpath")
        max_wait = kwargs.get("max_wait", FIND_ELEMENT_TIMEOUT)
        try:
            if not elem:
                if id:
                    locator = (By.ID, id)
                elif name:
                    locator = (By.NAME, name)
                elif tag_name:
                    locator = (By.TAG_NAME, tag_name)
                elif css_class:
                    locator = (By.CLASS_NAME, css_class)
                elif xpath:
                    locator = (By.XPATH, xpath)
            elem = WebDriverWait(browser, max_wait).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            raise KALiteTimeout("browser_activate_element timed out with keyword arguments: {0}".format(kwargs))
        else:
            WebDriverWait(browser, max_wait).until(EC.element_to_be_clickable(locator))
            elem.click()

    def browser_send_keys(self, keys, browser=None):
        """Convenience method to send keys to active_element in the browser"""
        browser = browser or self.browser
        browser.switch_to_active_element().send_keys(keys)

    def browser_check_django_message(self, message_type=None, contains=None, exact=None, num_messages=1):
        """Both central and distributed servers use the Django messaging system.
        This code will verify that a message with the given type contains the specified text."""

        # Get messages (and limit by type)
        if num_messages > 0:
            messages = WebDriverWait(self.browser, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "alert")))
        else:
            messages = []

        if isinstance(contains, str):  # make sure we only look at messages we're looking for.
            messages = [message for message in messages if contains in message.text]

        # Check that we got as many as expected
        if num_messages is not None:
            msg = "Make sure there are %d message(s), type='%s'." % \
                  (num_messages, message_type if message_type else "(any)")
            self.assertEqual(num_messages, len(messages), msg)

        for i, message in enumerate(messages):
            if type(contains) == list:
                contain = contains[i]
            else:
                contain = contains
            if type(exact) == list:
                exac = exact[i]
            else:
                exac = exact
            if contain is not None:
                self.assertIn(contain, message.text, "Make sure message contains '%s'" % contain)
            if exac is not None:
                self.assertEqual(exac, message.text, "Make sure message = '%s'" % exac)

    def browser_next_form_element(self, num_expected_links=None, max_tabs=10, browser=None):
        """
        Use keyboard navigation to traverse form elements.
        Skip any intervening elements that have tab stops (namely, links).

        If specified, validate the # links skipped, or the total # of tabs needed.
        """
        browser = browser or self.browser

        # Move to the next actable element.
        cur_element = browser.switch_to_active_element()
        self.browser_send_keys(Keys.TAB, browser=browser)
        num_tabs = 1

        # Loop until you've arrived at a form element
        num_links = 0
        while num_tabs <= max_tabs and \
                browser.switch_to_active_element().tag_name not in self.HtmlFormElements:
            num_links += browser.switch_to_active_element().tag_name == "a"
            self.browser_send_keys(Keys.TAB, browser=browser)
            num_tabs += 1

        # self.assertLessEqual(num_tabs, max_tabs,
        #                      "# of tabs exceeded max # of tabs (orig element: tag '%s' text '%s')." %
        #                      (cur_element.tag_name, cur_element.text))

        # if num_expected_links is not None:
        #     self.assertEqual(num_links, num_expected_links,
        #                      "Num links: actual (%d) != expected (%d)" % (num_links, num_expected_links))

        return num_tabs

    def browser_form_fill(self, keys="", browser=None):
        """
        Convenience function to send some keys to a form element,
        then traverse to the next form element.
        """
        browser = browser or self.browser
        if keys:
            self.browser_send_keys(keys, browser=browser)
        self.browser_next_form_element(browser=browser)

    def browser_wait_for_element(self, css_selector, max_wait_time=7, step_time=0.25):
        total_wait_time = 0
        element = None
        while total_wait_time < max_wait_time:

            time.sleep(step_time)
            total_wait_time += step_time
            try:
                element = self.browser.find_element_by_css_selector(css_selector)
                break
            except:
                pass
        return element

    def browser_wait_for_no_element(self, css_selector, max_wait_time=7, step_time=0.25):
        total_wait_time = 0
        while total_wait_time < max_wait_time:

            time.sleep(step_time)
            total_wait_time += step_time
            try:
                self.browser.find_element_by_css_selector(css_selector)
                pass
            except:
                break

    def browser_wait_for_js_condition(self, condition, max_wait_time=7, step_time=0.25):
        """
        Waits for the script in condition to return True.
        Warning: don't preface condition with "return"
        """
        total_wait_time = 0
        script = "return " + condition
        while total_wait_time < max_wait_time:

            time.sleep(step_time)
            total_wait_time += step_time
            if total_wait_time >= max_wait_time:
                raise KALiteTimeout("Timed out waiting for js condition {0}".format(condition))
            try:
                if self.browser.execute_script(script):
                    break
                else:
                    pass
            except WebDriverException:
                # possible if the object you want to exist is an attribute of an object
                # that doesn't yet exist, e.g. does_not_exist_yet.i_want_to_test_this_one
                pass

    def browser_wait_for_js_object_exists(self, obj_name, max_wait_time=7, step_time=0.25):
        exists_condition = "typeof(%s) !== 'undefined'" % obj_name
        self.browser_wait_for_js_condition(exists_condition, max_wait_time=max_wait_time, step_time=step_time)

    # Actual testing methods
    def empty_form_test(self, url, submission_element_id):
        """
        Submit forms with no values, make sure there are no errors.
        TODO(MCGallaspy): There's a lot wrong here -- why is a test hidden in a mixin? Can this be done with a client
          test case? And if not, can it be refactored into the behave framework?
        """

        self.browse_to(url)
        self.browser_activate_element(id=submission_element_id)  # explicitly set the focus, to start
        self.browser_send_keys(Keys.RETURN)
        # how to wait for page change?  Will reload the same page.
        self.assertNotEqual(self.browser_wait_for_element(".errorlist", max_wait_time=30), None, "Make sure there's an error.")

    def browser_accept_alert(self, sleep=1, text=None):
        """
        PhantomJS still have no support for modal dialogs (alert, confirm, prompt) javascript functions.

        See comment on `hacks_for_phantomjs()` method above.
        """
        alert = None

        WebDriverWait(self.browser, 30).until(EC.alert_is_present())
        alert = self.browser.switch_to_alert()
        try:
            if not self.is_phantomjs:
                alert = self.browser.switch_to_alert()
                if text:
                    alert.send_keys(text)
                alert.accept()
            # set some delay to allow browser to process / reload the page
            if sleep:
                time.sleep(sleep)
        except Exception as exc:
            logging.warn('==> Exception at browser.browser_set_alert(): %s' % exc)
        return alert

    def browser_click(self, selector):
        """
        PhantomJS does not support the click fully, specially on anchor tags so we use the hack script from
        `hacks_for_phantomjs()` method above.

        REF: http://stackoverflow.com/questions/13536752/phantomjs-click-a-link-on-a-page?rq=1
        """
        browser = self.browser
        if self.is_phantomjs:
            # MUST: Make sure we re-inject the script hacks because the browser may have been reloaded.
            hacks_for_phantomjs(browser)
            js = """
                var el = $('%s')[0];
                window.simulateClick(el);
            """ % selector
            browser.execute_script("%s" % js)
        else:
            elem = browser.find_element_by_css_selector(selector)
            elem.click()

    def browser_click_and_accept(self, selector, sleep=1, text=None):
        """
        Shorthand to click on a link/button, show a modal dialog, then accept it.

        Use the fixed quirks on PhantomJS/GhostDriver on modal dialogs and clicking on anchor tags.

        See comment on `hacks_for_phantomjs()` method above.
        """
        self.browser_click(selector)
        alert = self.browser_accept_alert(sleep=sleep, text=text)
        return alert


    def browser_register_user(self, username, password, first_name="firstname",
                              last_name="lastname", facility_name=None,
                              stay_logged_in=False):
        """
        Tests that a user can register.
        This method will fail if you haven't created an admin and a facility.
        (See CreateAdminMixin and CreateFacilityMixin.)
        """

        self.assertTrue(self._admin_exists(), "No admin user exists")
        self.assertTrue(self._facility_exists(), "No facility exists")

        # Expected results vary based on whether a user is logged in or not.
        if not stay_logged_in:
            self.browser_logout_user()

        register_url = self.reverse("facility_user_signup")
        self.browse_to(register_url)  # Load page

        # Part 1: REGISTER
        if facility_name and self.browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element("id_facility")
            self.browser_send_keys(facility_name)
        self.browser_activate_element(id="id_username")  # explicitly set the focus, to start
        self.browser_form_fill(username)
        self.browser_form_fill(first_name)
        self.browser_form_fill(last_name)
        self.browser_form_fill(password)
        self.browser_form_fill(password)  # password (again)
        self.browser.find_element_by_id("id_username").submit()

    def browser_login_user(self, username, password, facility_name=None, browser=None):
        try:
            facility = Facility.objects.get(name=facility_name)
        except Facility.DoesNotExist:
            facility = Facility.objects.all()[0] if Facility.objects.all() else None
        data = json.dumps({
            "username": username,
            "password": password,
            "facility": facility.id if facility else "",
        })
        url = self.reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "login/"
        self.__request(method="POST", url=url, data=data, browser=browser)
        self.browser.refresh()


    def browser_login_admin(self, username=None, password=None, browser=None):
        self.browser_login_user(username=username, password=password, browser=browser)

    def browser_login_teacher(self, username, password, facility_name=None, browser=None):
        self.browser_login_user(
            username=username,
            password=password,
            facility_name=facility_name,
            browser=browser,
        )

    def browser_login_student(self, username, password, facility_name=None, exam_mode_on=False, browser=None):
        """
        Consider that student may be redirected to the exam page when Settings.EXAM_MODE_ON is set.
        """
        self.browser_login_user(
            username=username,
            password=password,
            facility_name=facility_name,
            browser=browser,
        )

    def browser_logout_user(self, browser=None):
        url = self.reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "logout/"
        self.__request(method="GET", url=url, data="")
        self.browser.refresh()


    def __request(self, method, url, data, browser=None):
        browser = browser or self.browser
        browser.get(self.reverse("homepage"))  # Send requests from the same domain
        browser.execute_script("""
                var req = new XMLHttpRequest();
                req.open("{method}", "{url}", true);
                req.setRequestHeader("Content-Type", "application/json");
                window.FLAG = false;
                req.onreadystatechange = function () {{
                    if( req.readyState === 4 ) {{
                        window.FLAG = true;
                        window.DATA = JSON.parse(req.responseText);
                    }}
                }};
                req.send('{data}');
            """.format(method=method, url=url, data=data)  # One must escape '{' and '}' by doubling them
        )
        self.browser_wait_for_js_condition("window.FLAG")
        return browser.execute_script("return window.DATA")


    def browser_is_logged_in(self, expected_username=None, browser=None):
        url = self.reverse("api_dispatch_list", kwargs={"resource_name": "user"}) + "status/"
        data = self.__request(method="GET", url=url, data="", browser=browser)
        return data.get("is_logged_in", False)


    def fill_form(self, input_id_dict):
        """
        Fill the form with the values of the given a dictionary
        where the keys are the ids of the input fields
        """
        for key in input_id_dict.keys():
            inputElement = self.browser.find_element_by_id(key)
            inputElement.clear()
            inputElement.send_keys(input_id_dict[key])
            time.sleep(0.5)

    @classmethod
    def _admin_exists(cls):
        return User.objects.filter(is_superuser=True).exists()

    @classmethod
    def _facility_exists(cls):
        return Facility.objects.all().exists()

    def browse_to_random_video(self):
        available = False
        video = get_random_content(limit=1)[0]
        video_url = video['path']
        self.browse_to(self.reverse("learn") + video_url)

    def browser_get_points(self):
        # The following commented line of code returns an element with blank text,
        # possibly due to a race condition, hence querying the element with js which "just works"
        # points_elem = self.browser.find_element_by_id("points")
        # Ensure the element has been populated by triggering an event
        self.browser_wait_for_js_object_exists("window.statusModel");
        self.browser.execute_script("window.statusModel.trigger(\"change:points\");")
        points_text = self.browser.execute_script("return $('#points').text();")
        self.assertTrue(bool(points_text), "Failed fetching contents of #points element, got {0}".format(repr(points_text)))
        return int(re.search(r"(\d+)", points_text).group(1))

