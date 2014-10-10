import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from django.utils.translation import ugettext as _

from ..browser import browse_to, setup_browser, wait_for_page_change


class BrowserActionMixins(object):

    max_wait_time = 4

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

    def wait_for_page_change(self, source_url, wait_time=0.1, max_retries=None):
        """
        When testing, we have to make sure that the page has loaded before testing the resulting page.
        """

        if not max_retries:
            max_retries = int(self.max_wait_time/float(wait_time))
        return wait_for_page_change(self.browser, source_url, wait_time=wait_time, max_retries=max_retries)

    def browser_activate_element(self, elem=None, id=None, name=None, tag_name=None, browser=None):
        """
        Given the identifier to a page element, make it active.
        Currently done by clicking TODO(bcipolli): this won't work for buttons,
        so find another way when that becomes an issue.
        """
        browser = browser or self.browser
        if not elem:
            if id:
                elem = browser.find_element_by_id(id)
            elif name:
                elem = browser.find_element_by_name(name)
            elif tag_name:
                elem = browser.find_element_by_tag_name(tag_name)
        elem.click()

    def browser_send_keys(self, keys, browser=None):
        """Convenience method to send keys to active_element in the browser"""
        browser = browser or self.browser
        browser.switch_to_active_element().send_keys(keys)

    def browser_check_django_message(self, message_type=None, contains=None, exact=None, num_messages=1):
        """Both central and distributed servers use the Django messaging system.
        This code will verify that a message with the given type contains the specified text."""

        WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))

        # Get messages (and limit by type)
        messages = self.browser.find_elements_by_class_name("alert")

        # Check that we got as many as expected
        if num_messages is not None:
            msg = "Make sure there are %d message(s), type='%s'." % \
                  (num_messages, message_type if message_type else "(any)")
            self.assertEqual(num_messages, len(messages), msg)

        for message in messages:
            if contains is not None:
                self.assertIn(contains, message.text, "Make sure message contains '%s'" % contains)
            if exact is not None:
                self.assertEqual(exact, message.text, "Make sure message = '%s'" % exact)

    def browser_wait_for_ajax_calls_to_finish(self):
            while True:
                num_ajax_calls = int(self.browser.execute_script('return jQuery.active;'))
                if num_ajax_calls > 0:
                    time.sleep(1)
                else:
                    break

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

    def browser_wait_for_element(self, css_selector, max_wait_time=4, step_time=0.25):
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

    def browser_wait_for_no_element(self, css_selector, max_wait_time=4, step_time=0.25):
        total_wait_time = 0
        while total_wait_time < max_wait_time:

            time.sleep(step_time)
            total_wait_time += step_time
            try:
                self.browser.find_element_by_css_selector(css_selector)
                pass
            except:
                break

    # Actual testing methods
    def empty_form_test(self, url, submission_element_id):
        """
        Submit forms with no values, make sure there are no errors.
        """

        self.browse_to(url)
        self.browser_activate_element(id=submission_element_id)  # explicitly set the focus, to start
        self.browser_send_keys(Keys.RETURN)
        # how to wait for page change?  Will reload the same page.
        self.assertNotEqual(self.browser_wait_for_element(".errorlist"), None, "Make sure there's an error.")

    def browser_accept_alert(self, sleep=1, text=None):
        """
        PhantomJS still have no support for modal dialogs (alert, confirm, prompt) javascript functions.

        See comment on `hacks_for_phantomjs()` method above.
        """
        alert = None

        WebDriverWait(self.browser, 5).until(EC.alert_is_present())
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
        """Tests that a user can register"""

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
        """
        Tests that an existing admin user can log in.
        """
        browser = browser or self.browser

        login_url = self.reverse("login")
        self.browse_to(login_url, browser=browser)  # Load page

        # Focus should be on username, password and submit
        #   should be accessible through keyboard only.
        if facility_name and browser.find_element_by_id("id_facility").is_displayed():
            self.browser_activate_element(id="id_facility")
            self.browser_send_keys(facility_name)

        username_field = browser.find_element_by_id("id_username")
        username_field.clear()  # clear any data
        username_field.click()  # explicitly set the focus, to start
        self.browser_form_fill(username, browser=browser)
        self.browser_form_fill(password, browser=browser)
        username_field.submit()
        # self.browser_send_keys(Keys.RETURN)

        # wait for 5 seconds for the page to refresh
        WebDriverWait(browser, 5).until(EC.staleness_of(username_field))

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
        browser = browser or self.browser
        if self.browser_is_logged_in(browser=browser):
            # Since logout redirects to the homepage, browse_to will fail (with no good way to avoid).
            #   so be smarter in that case.
            homepage_url = self.reverse("homepage")
            logout_url = self.reverse("logout")
            if homepage_url == browser.current_url:
                browser.get(logout_url)
            else:
                self.browse_to(logout_url, browser=browser)
            self.assertEqual(homepage_url, browser.current_url, "Logout redirects to the homepage")
            self.assertFalse(self.browser_is_logged_in(), "Make sure that user is no longer logged in.")

    def browser_is_logged_in(self, expected_username=None, browser=None):
        # Two ways to be logged in:
        # 1. Student: #logged-in-name is username
        # 2. Admin: #logout contains username
        browser = browser or self.browser
        try:
            logged_in_name = browser.find_element_by_css_selector("#sitepoints > span:nth-child(1)").text.strip()
            logout_text = browser.find_element_by_id("nav_logout").text.strip()
        except NoSuchElementException:
            # We're on an unrecognized webpage
            return False

        username_text = logged_in_name or logout_text[0:-len(" (%s)" % _("Logout"))]

        # Just checking to see if ANYBODY is logged in
        if not expected_username:
            return username_text != ""
        # Checking to see if Django user, or user with missing names is logged in
        #   (then username displays)
        elif username_text.lower() == expected_username.lower():
            return True
        # Checking to see if a FacilityUser with a filled-in-name is logged in
        else:
            user_obj = FacilityUser.objects.filter(username=expected_username)
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()

            user_obj = FacilityUser.objects.filter(username__iexact=expected_username)
            if user_obj.count() != 0:  # couldn't find the user, they can't be logged in
                return username_text.lower() == user_obj[0].get_name().lower()
            else:
                assert username_text == "", "Impossible for anybody to be logged in."


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
