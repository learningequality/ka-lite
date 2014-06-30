"""
"""
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import DatabaseError

from .base import create_test_admin, KALiteTestCase

logging = settings.LOG

browser = None  # persistent browser


def setup_test_env(browser_type="Firefox", test_user="testadmin", test_password="test",
                   test_email="test@learningequality.org", persistent_browser=False):
    """Create a django superuser, and connect to the specified browser.
    peristent_browser: keep a static handle to the browser, rather than
      re-launch for every testcase.  True currently doesn't work well, so just do False :("""

    global browser

    # Add the test user
    try:
        admin_user = User.objects.get(username=test_user)
    except ObjectDoesNotExist:
        admin_user = create_test_admin(username=test_user, password=test_password, email=test_email)

    # Launch the browser
    if not persistent_browser or (persistent_browser and not browser):
        local_browser = getattr(webdriver, browser_type)()  # Get local session of browser
        if persistent_browser:  # share browser across tests
            browser = local_browser
    else:
        local_browser = browser

    hacks_for_phantomjs(local_browser)

    return (local_browser, admin_user, test_password)


def hacks_for_phantomjs(browser):
    """
    HACK: If using PhantomJS, override the window.alert()/confirm()/prompt() functions to return true because
    the GhostDriver does not support modal dialogs (alert, confirm, prompt).

    What we do is override the alert/confirm/prompt functions so any call that expects the dialog with return true.

    REF: http://stackoverflow.com/questions/15708518/how-can-i-handle-an-alert-with-ghostdriver-via-python
    REF: https://groups.google.com/forum/#!topic/phantomjs/w_rKkFJ0g8w
    REF: http://stackoverflow.com/questions/13536752/phantomjs-click-a-link-on-a-page?rq=1
    """
    if isinstance(browser, webdriver.PhantomJS):
        js = """
            window.confirm = function(message) {
                return true;
            }
            window.alert = window.prompt = window.confirm;

            // REF: http://stackoverflow.com/questions/13536752/phantomjs-click-a-link-on-a-page?rq=1
            // REF: http://stackoverflow.com/questions/2705583/how-to-simulate-a-click-with-javascript/2706236#2706236
            window.eventFire = function(el, etype) {
                if (el.fireEvent) {
                    el.fireEvent('on' + etype);
                } else {
                    var evObj = document.createEvent('Events');
                    evObj.initEvent(etype, true, false);
                    el.dispatchEvent(evObj);
                }
            };

            // shortcut of above method
            window.simulateClick = function(el) {
                var e = document.createEvent('MouseEvents');
                e.initEvent( 'click', true, true );
                el.dispatchEvent(e);
            };
        """
        browser.execute_script("%s" % js)


def browse_to(browser, dest_url, wait_time=0.1, max_retries=50):
    """Given a selenium browser, open the given url and wait until the browser has completed."""

    if dest_url == browser.current_url:
        return True

    source_url = browser.current_url
    page_source = browser.page_source

    browser.get(dest_url)

    return wait_for_page_change(browser, source_url=source_url, page_source=page_source,
                                wait_time=wait_time, max_retries=max_retries)


def wait_for_page_change(browser, source_url=None, page_source=None, wait_time=0.1, max_retries=50):
    """Given a selenium browser, wait until the browser has completed.
    Code taken from: https://github.com/dragoon/django-selenium/blob/master/django_selenium/testcases.py"""

    for i in range(max_retries):
        if source_url is not None and browser.current_url != source_url:
            break
        elif page_source is not None and browser.page_source != page_source:
            break
        else:
            time.sleep(wait_time)

    return browser.current_url != source_url


class BrowserTestCase(KALiteTestCase):
    """
    A base test case for Selenium, providing helper methods for generating
    clients and logging in profiles.
    """

    persistent_browser = False

    HtmlFormElements = ["form", "input", "textarea", "label", "fieldset", "legend", "select", "optgroup",
                        "option", "button", "datalist", "keygen", "output"]  # not all act as tab stops, but ...

    def __init__(self, *args, **kwargs):
        self.max_wait_time = kwargs.get("max_wait_time", 30)
        # DJANGO_CHANGE(aron):
        # be able to support headless tests, which run PhantomJS
        # instead of showing running a full-blown browser.
        # Since there's no elegant way to pass options to testcases,
        # we pass it through the settings module, with HEADLESS
        # essentially acting as a global variable. See:
        # python-packages/django/core/management/commands/test.py
        if getattr(settings, 'HEADLESS', None):
            self.browser_list = ['PhantomJS']
        else:
            self.browser_list = ['Firefox', 'Chrome', 'Ie', 'Opera']
        super(BrowserTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        """Create a browser to use for test cases.  Try a bunch of different browsers; hopefully one of them works!"""

        super(BrowserTestCase, self).setUp()

        # Clear the session cache after every test case, to keep things clean.
        Session.objects.all().delete()

        # # Can use already launched browser.
        # if self.persistent_browser:
        #     kwargs = {
        #         'persistent_browser': self.persistent_browser
        #     }
        #     # If `browser_list` exists and has element, use the first element on the list instead of defaulting
        #     # to `Firefox` browser.  This will have `PhantomJS` if `settings.HEADLESS` is specified.
        #     # See `__init__` method.
        #     if self.browser_list and len(self.browser_list) > 0:
        #         kwargs['browser_type'] = self.browser_list[0]
        #     (self.browser, self.admin_user, self.admin_pass) = setup_test_env(**kwargs)
        #
        # # Must create a new browser to use
        # else:
        for browser_type in self.browser_list:
            try:
                kwargs = {
                    'persistent_browser': self.persistent_browser,
                    'browser_type': browser_type
                }
                (self.browser, self.admin_user, self.admin_pass) = setup_test_env(**kwargs)
                # (self.browser, self.admin_user, self.admin_pass) = setup_test_env(browser_type=browser_type)
                break
            except DatabaseError:
                raise
            except Exception as e:
                import traceback
                print traceback.format_exc()
                logging.error("Could not create browser %s through selenium: %s" % (browser_type, e))

    def tearDown(self):
        if not self.persistent_browser and hasattr(self, "browser") and self.browser:
            self.browser.quit()
        return super(BrowserTestCase, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        global browser
        if cls.persistent_browser and browser:
            browser.quit()
            browser = None
        return super(BrowserTestCase, cls).tearDownClass()

    def browse_to(self, *args, **kwargs):
        """
        When testing, we have to make sure that the page has loaded before testing the resulting page.

        Three ways to specify the url to browse to:
        1. First positional argument
        2. dest_url keyword argument
        3. reverse lookup of url_name argument.
        """
        if args:
            assert "dest_url" not in kwargs
            dest_url = args[0]
        elif "dest_url" in kwargs:
            assert "url_name" not in kwargs
            dest_url = kwargs["dest_url"]
        elif "url_name" in kwargs:
            kwargs["dest_url"] = self.reverse(kwargs["url_name"])
            del kwargs["url_name"]
            dest_url = kwargs["dest_url"]
        else:
            raise Exception("Must specify the destination url.")

        browse_to(self.browser, *args, **kwargs)

    def wait_for_page_change(self, source_url, wait_time=0.1, max_retries=None):
        """
        When testing, we have to make sure that the page has loaded before testing the resulting page.
        """

        if not max_retries:
            max_retries = int(self.max_wait_time/float(wait_time))
        return wait_for_page_change(self.browser, source_url, wait_time=wait_time, max_retries=max_retries)

    def browser_activate_element(self, elem=None, id=None, name=None, tag_name=None):
        """
        Given the identifier to a page element, make it active.
        Currently done by clicking TODO(bcipolli): this won't work for buttons,
        so find another way when that becomes an issue.
        """

        if not elem:
            if id:
                elem = self.browser.find_element_by_id(id)
            elif name:
                elem = self.browser.find_element_by_name(name)
            elif tag_name:
                elem = self.browser.find_element_by_tag_name(tag_name)
        elem.click()

    def browser_send_keys(self, keys):
        """Convenience method to send keys to active_element in the browser"""
        self.browser.switch_to_active_element().send_keys(keys)

    def browser_check_django_message(self, message_type=None, contains=None, exact=None, num_messages=1):
        """Both central and distributed servers use the Django messaging system.
        This code will verify that a message with the given type contains the specified text."""

        time.sleep(2)  # wait for the message to get created via AJAX

        # Get messages (and limit by type)
        messages = self.browser.find_elements_by_class_name("alert")
        if message_type:
            messages = [m for m in messages if message_type in m.get_attribute("class")]

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

    def browser_next_form_element(self, num_expected_links=None, max_tabs=10):
        """
        Use keyboard navigation to traverse form elements.
        Skip any intervening elements that have tab stops (namely, links).

        If specified, validate the # links skipped, or the total # of tabs needed.
        """

        # Move to the next actable element.
        cur_element = self.browser.switch_to_active_element()
        self.browser_send_keys(Keys.TAB)
        num_tabs = 1

        # Loop until you've arrived at a form element
        num_links = 0
        while num_tabs <= max_tabs and \
                self.browser.switch_to_active_element().tag_name not in BrowserTestCase.HtmlFormElements:
            num_links += self.browser.switch_to_active_element().tag_name == "a"
            self.browser_send_keys(Keys.TAB)
            num_tabs += 1

        self.assertLessEqual(num_tabs, max_tabs,
                             "# of tabs exceeded max # of tabs (orig element: tag '%s' text '%s')." %
                             (cur_element.tag_name, cur_element.text))

        if num_expected_links is not None:
            self.assertEqual(num_links, num_expected_links,
                             "Num links: actual (%d) != expected (%d)" % (num_links, num_expected_links))

        return num_tabs

    def browser_form_fill(self, keys=""):
        """
        Convenience function to send some keys to a form element,
        then traverse to the next form element.
        """
        if keys:
            self.browser_send_keys(keys)
        self.browser_next_form_element()

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

    def browser_accept_alert(self, sleep=1):
        """
        PhantomJS still have no support for modal dialogs (alert, confirm, prompt) javascript functions.

        See comment on `hacks_for_phantomjs()` method above.
        """
        alert = None
        try:
            if not isinstance(self.browser, webdriver.PhantomJS):
                alert = self.browser.switch_to_alert()
                alert.accept()
            # set some delay to allow browser to process / reload the page
            if sleep:
                time.sleep(sleep)
        except Exception as exc:
            logging.warn('==> Exception at browser.browser_set_alert(): %s' % exc)
        return alert

    def browser_click(self, elem, selector=None):
        """
        PhantomJS does not support the click fully, specially on <a> tags so send a Return key instead.

        REF: http://stackoverflow.com/questions/13536752/phantomjs-click-a-link-on-a-page?rq=1
        """
        if isinstance(self.browser, webdriver.PhantomJS):
            if not selector:
                elem.send_keys(Keys.RETURN)
            else:
                # MUST: Make sure we re-inject the script hacks because the browser may have been reloaded.
                hacks_for_phantomjs(self.browser)
                js = """
                    var el = $('%s')[0];
                    window.simulateClick(el);
                """ % selector
                self.browser.execute_script("%s" % js)
        else:
            elem.click()

    def browser_click_and_accept(self, elem, selector, sleep=1):
        """
        Shorthand to click on a link/button, show a modal dialog, then accept it.

        Use the fixed quirks on PhantomJS/GhostDriver on modal dialogs and clicking on anchor tags.

        See comment on `hacks_for_phantomjs()` method above.
        """
        self.browser_click(elem=elem, selector=selector)
        self.browser_accept_alert(sleep=sleep)