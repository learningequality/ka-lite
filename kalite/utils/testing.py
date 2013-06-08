import copy
import decorator
import logging
import time
import os
import shutil
import sys
import platform
import tempfile
import unittest
from selenium import webdriver
from StringIO import StringIO

from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test import TestCase, LiveServerTestCase
from django_snippets._mkdir import _mkdir

import settings
from kalite.utils.django_utils import call_command_with_output
from playground.test_tools.mount_branch import KaLiteServer, KaLiteSelfZipProject


def x_only(f, cond, msg):
    """Decorator"""

    if f.__class__.__name__ == "type":
        @unittest.skipIf(cond, msg)
        class wrapped_class(f):
            pass
        return wrapped_class
        
    else:
        @unittest.skipIf(cond, msg)
        def wrapped_fn(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_fn

def main_only(f):
    return x_only(f, settings.CENTRAL_SERVER, "Distributed server test")

def central_only(f):
    return x_only(f, not settings.CENTRAL_SERVER, "Central server test")
    
         
def add_to_local_settings(var, val):
    fh = open(settings.PROJECT_PATH + "/local_settings.py","a")
    fh.write("\n%s = %s" % (var,str(val)))
    fh.close()
        
def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""
    
    test_admin = User.objects.create_superuser(username, email, password)
    logging.debug('Created user "%s"' % username)

    # You'll need to log him in before you can send requests through the client
    client = Client()
    assert client.login(username=test_admin.username, password=password)

    # set dummy password, so it can be passed around
    test_admin.password = password
    assert client.login(username=test_admin.username, password=password)
    
    return test_admin
    
    
browser = None
def setup_test_env(browser_type="Firefox", test_user="test", test_password="test", test_email="test@learningequality.org", persistent_browser=False):
    """Create a django superuser, and connect to the specified browser.
    peristent_browser: keep a static handle to the browser, rather than 
      re-launch for every testcase.  True currently doesn't work well, so just do False :("""
      
    global browser
        
    # Add the test user
    admin_user = create_test_user(username=test_user, password=test_password, email=test_email)
    
    # Launch the browser
    if not persistent_browser or (persistent_browser and not browser):
        local_browser = getattr(webdriver, browser_type)() # Get local session of firefox
        if persistent_browser: # share browser across tests
            browser = local_browser
    else:
        local_browser = browser
       
    return (local_browser,admin_user)
            


def wait_for_page_change(browser, source_url, max_retries=10):
    """Given a selenium browser, wait until the browser has completed.
    Code taken from: https://github.com/dragoon/django-selenium/blob/master/django_selenium/testcases.py"""

    for i in range(max_retries):
        if browser.current_url == source_url:
            time.sleep(100)
        else:
            break;

    return browser.current_url != source_url
    
    

class KALiteTestCase(LiveServerTestCase):
    def __init__(self, *args, **kwargs):
        #create_test_admin()
        return super(KALiteTestCase, self).__init__(*args, **kwargs)
        
    def reverse(self, url_name):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name)

    
class BrowserTestCase(KALiteTestCase):
    """
    A base test case for Selenium, providing helper methods for generating
    clients and logging in profiles.
    """
    persistent_browser = False
    
    def setUp(self):
        (self.browser,self.admin_user) = setup_test_env(persistent_browser=self.persistent_browser)
        
    def tearDown(self):
        if not self.persistent_browser:
            self.browser.quit()
        
    def wait_for_page_change(self, source_url, max_retries=10):
        return wait_for_page_change(self.browser, source_url, max_retries)
    
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
    
    def capture_stdout(self, cmdargs):
        """Captures output to stdout when a particular test command is run.
        cmdargs: first arg is the function, all other args are positional args.
           there should be a better way to do this, but I'm not sure what it is yet."""
        
        # Parse out function and args
        fn = cmdargs[0]
        args = cmdargs[1:]
        
        # Save old stdout stream.  Save stdout string.  Restore old stdout stream
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            fn(args)
            output = out.getvalue().strip()
        except Exception as e:
            output = e.message
        finally:
            sys.stdout = saved_stdout        

        return output

   
class KALiteCentralBrowserTestCase(BrowserTestCase):
    """Base class for central server test cases"""
    pass
    
    
class KALiteLocalBrowserTestCase(BrowserTestCase):
    pass


class KALiteEcosystemTestCase(KALiteTestCase):
    """A testcase involving an "ecosystem" of KA Lite servers: 1 central server and two distributed servers
    on the same zone.
    
    Subclasses could look at more complex scenarios."""
    
    # TODO(bcipolli) move setup and teardown code to class (not instance);
    #   not sure how to tear down in this case, though...............
        
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger("kalite")
        self.zip_file = tempfile.mkstemp()[1]
        self.base_dir = tempfile.mkdtemp()
                
        return super(KALiteEcosystemTestCase, self).__init__(*args, **kwargs)

    def setup_ports(self):        
        self.port = int(self.live_server_url.split(":")[2])

        assert os.environ.get("DJANGO_LIVE_TEST_SERVER_ADDRESS",""), "This testcase can only be run running under the liveserver django test option.  For KA Lite, this should be set up by our TestRunner (which is set up in settings.py)"
        self.open_ports = [int(p) for p in os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'].split(":")[1].split("-")]
        if len(self.open_ports) != 2:
            raise Exception("Unable to parse ports. Use a simple range (8000-8080)")
        self.open_ports = set(range(self.open_ports[0], self.open_ports[1]+1)) - {self.port,}


    def setUp(self, *args, **kwargs):
        """Package two servers just like this one, and mount."""
        
        self.setup_ports()

        # Make sure the setup is 2 local, 1 central
        # First is for this server, 2 and 3 are for the others
        server_types = ["central" if settings.CENTRAL_SERVER else "local", 'local' if settings.CENTRAL_SERVER else 'central', 'local2']

        self.log.info("Setting up ecosystem: your server [%s; port %d], plus %s servers" % (server_types[0], self.port, str(server_types[1:])))


        # Create a zip file 
        self.log.info("Creating zip package for your server; please wait.")
        out = call_command_with_output("package_for_download", platform=platform.system(), locale='en', file=self.zip_file)
        self.log.info("Completed zip package for your server.")
        
        # Copy, install, and start the servers
        self.log.info("Installing two servers; please wait.")
        kap = KaLiteSelfZipProject(base_dir=self.base_dir, zip_file=self.zip_file, persistent_ports=False)
        kap.mount_project(server_types=server_types[1:], host="127.0.0.1", open_ports=self.open_ports, port_map={server_types[0]: self.port})

        # Save all servers to be accessible
        own_server = KaLiteServer(base_dir=settings.PROJECT_PATH+"/../", server_type=server_types[0], port=self.port, central_server_host="127.0.0.1", central_server_port = kap.port_map['central'])
        self.servers = copy.copy(kap.servers)
        self.servers[server_types[0]] = own_server
        
        return super(KALiteEcosystemTestCase, self).setUp(*args, **kwargs)
        
    
    def tearDown(self):
        self.log.info("Tearing down ecosystem test servers")
        shutil.rmtree(self.base_dir)
        os.remove(self.zip_file)
        
