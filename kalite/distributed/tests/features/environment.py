from behave import *
from django.test.testcases import LiveServerTestCase
from selenium import webdriver
from urlparse import urljoin

def before_all(context):
    # What am I using from this?
    # It sets up a test database
    # and runs an instance of the server
    live_server = context.live_server = HijackTestCase('test_something')
    live_server.setUpClass()

    def browser_url(url):
        return urljoin(live_server.live_server_url, url)
    
    context.browser_url = browser_url


def after_all(context):
    context.live_server.tearDownClass()


def before_scenario(context, scenario):
    browser = context.browser = webdriver.Firefox()


def after_scenario(context, scenario):
    context.browser.close()        


class HijackTestCase(LiveServerTestCase):

    def test_something(self):
        pass
