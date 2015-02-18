"""
"""
import time
from selenium import webdriver

from django.conf import settings

logging = settings.LOG

browser = None  # persistent browser


def setup_browser(browser_type="Firefox"):
    """Setup the browser. `browser_type` sets up the type of browser loaded by selenium."""

    browser = getattr(webdriver, browser_type)()
    hacks_for_phantomjs(browser)

    return browser

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

            // shorter alternative of above method
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
