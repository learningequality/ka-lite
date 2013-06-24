import time
from selenium import webdriver

from kalite import settings
from utils.testing.base import create_test_admin, KALiteTestCase


browser = None # persistent browser
def setup_test_env(browser_type="Firefox", test_user="testadmin", test_password="test", test_email="test@learningequality.org", persistent_browser=False):
    """Create a django superuser, and connect to the specified browser.
    peristent_browser: keep a static handle to the browser, rather than 
      re-launch for every testcase.  True currently doesn't work well, so just do False :("""
      
    global browser
        
    # Add the test user
    admin_user = create_test_admin(username=test_user, password=test_password, email=test_email)
    
    # Launch the browser
    if not persistent_browser or (persistent_browser and not browser):
        local_browser = getattr(webdriver, browser_type)() # Get local session of firefox
        if persistent_browser: # share browser across tests
            browser = local_browser
    else:
        local_browser = browser
       
    return (local_browser,admin_user,test_password)
            

def browse_to(browser, dest_url, wait_time=0.1, max_retries=50):
    """Given a selenium browser, open the given url and wait until the browser has completed."""
    if dest_url == browser.current_url:
        return True
         
    source_url = browser.current_url
    page_source = browser.page_source
    
    browser.get(dest_url)
    
    return wait_for_page_change(browser, source_url=source_url, page_source=page_source, wait_time=wait_time, max_retries=max_retries)
    

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
    def __init__(self, *args, **kwargs):
        self.persistent_browser = False
        super(BrowserTestCase, self).__init__(*args, **kwargs)
        
    def setUp(self):
        """Create a browser to use for test cases.  Try a bunch of different browsers; hopefully one of them works!"""
        
        # Can use already launched browser.
        if self.persistent_browser:
            (self.browser,self.admin_user,self.admin_pass) = setup_test_env(persistent_browser=self.persistent_browser)
            
        # Must create a new browser to use
        else:
            for browser_type in ["Firefox", "Chrome", "Ie", "Opera"]:
                try:
                    (self.browser,self.admin_user,self.admin_pass) = setup_test_env(browser_type=browser_type)
                    break
                except Exception as e:
                    settings.LOG.debug("Could not create browser %s through selenium: %s" % (browser_type, e))

        
    def tearDown(self):
        if not self.persistent_browser:
            self.browser.quit()

        
    def browse_to(self, dest_url, wait_time=0.1, max_retries=50):
        """When testing, we have to make sure that the page has loaded before testing the resulting page."""

        self.assertTrue(browse_to(self.browser, dest_url=dest_url, wait_time=wait_time, max_retries=max_retries), "Browsing to '%s'" % dest_url)
        
        
    def wait_for_page_change(self, source_url, wait_time=0.1, max_retries=50):
        """When testing, we have to make sure that the page has loaded before testing the resulting page."""
         
        return wait_for_page_change(self.browser, source_url, wait_time=wait_time, max_retries=max_retries)

    
    def browser_activate_element(self, elem=None, id=None, name=None, tag_name=None):
        """Given the identifier to a page element, make it active.
        Currently done by clicking TODO(bcipolli): this won't work for buttons, 
        so find another way when that becomes an issue."""
        
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
        

    def check_django_message(self, message_type=None, contains=None, exact=None, num_messages=1):
        """Both central and distributed servers use the Django messaging system.
        This code will verify that a message with the given type contains the specified text."""
        
        time.sleep(0.50) # wait for the message to get created via AJAX

        # Get messages (and limit by type)    
        messages = self.browser.find_elements_by_class_name("message")
        if type:
            messages = [m for m in messages if message_type in m.get_attribute("class")]

        # Check that we got as many as expected
        if num_messages is not None:
            self.assertEqual(num_messages, len(messages)), "Make sure there are %d message(s), type='%s'." % (num_messages, message_type if message_type else "(any)")
        
        for message in messages:
            if contains is not None:
                self.assertIn(contains, message.text, "Make sure message contains '%s'" % contains)
            if exact is not None:
                self.assertEqual(exact, message.text, "Make sure message = '%s'" % exact)

           