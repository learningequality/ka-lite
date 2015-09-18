"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.
"""
import os
import tempfile
import shutil
import sauceclient as sc

from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connections

from kalite.testing.base import KALiteTestCase
from kalite.testing.behave_helpers import login_as_admin, login_as_coach, logout, login_as_learner

from securesync.models import Zone, Device, DeviceZone

def before_all(context):
    pass

def after_all(context):
    pass

def before_feature(context, feature):
    pass

def after_feature(context, feature):
    pass

def setup_sauce_browser(context):
    """
    Use saucelabs remote webdriver. Has side effects on the passed in behave context.

    :param context: the behave context
    :return: none, but has side effects. Adds properties "sauce" and "browser" to context.
    """
    # based on http://saucelabs.com/examples/example.py
    username = os.environ.get('SAUCE_USERNAME')
    access_key = os.environ.get('SAUCE_ACCESS_KEY')
    circle_build = os.environ.get('CIRCLE_BUILD_NUM')
    circle_node = os.environ.get('CIRCLE_NODE_INDEX')
    
    tunnel_id = "{build}-{node}".format(build=circle_build, node=circle_node)
    context.sauce = sc.SauceClient(username, access_key)
    sauce_url = "http://{username}:{access_key}@ondemand.saucelabs.com:80/wd/hub".format(username=username,
                                                                                         access_key=access_key)

    profile = webdriver.FirefoxProfile()
    if "download_csv" in context.tags:
        # Let csv files be downloaded automatically. Can be accessed using context.download_dir
        context.download_dir = tempfile.mkdtemp()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", context.download_dir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
        context.browser = webdriver.Firefox(firefox_profile=profile)  # Use local browser for this particular test
    else:
        desired_capabilities = DesiredCapabilities.FIREFOX.copy()
        desired_capabilities["tunnelIdentifier"] = tunnel_id
        try:
            context.browser = webdriver.Remote(desired_capabilities=desired_capabilities,
                                               browser_profile=profile,
                                               command_executor=sauce_url)
        except WebDriverException:
            print("Couldn't establish a connection to saucelabs. Using a local Firefox WebDriver instance.")
            del context.sauce
            context.browser = webdriver.Firefox(firefox_profile=profile)

def setup_local_browser(context):
    """
    Use local webdriver. Has side effects on the passed in behave context.

    :param context: the behave context
    :return: none, but has side effects. Adds property "browser" to context.
    """

    profile = webdriver.FirefoxProfile()
    if "download_csv" in context.tags:
        # Let csv files be downloaded automatically. Can be accessed using context.download_dir
        context.download_dir = tempfile.mkdtemp()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", context.download_dir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    context.browser = webdriver.Firefox(firefox_profile=profile)

# FYI: context.tags contains feature tags + scenario tags.
def before_scenario(context, scenario):
    database_setup(context)

    if "registered_device" in context.tags:
        do_fake_registration()

    if os.environ.get("TRAVIS", False):  # Indicates we're running on remote build server
        setup_sauce_browser(context)
    else:
        setup_local_browser(context)

    context.logged_in = False
    # A superuser now needs to exist or UI is blocked by a modal.
    # https://github.com/learningequality/ka-lite/pull/3668
    if not User.objects.filter(is_superuser=True).exists():
        assert User.objects.create_superuser(
            username='superusername',
            password='superpassword',
            email='super@email.com'
        ), "Didn't create an admin user"
    if "as_admin" in context.tags:
        context.logged_in = True
        login_as_admin(context)
    elif "as_coach" in context.tags:
        context.logged_in = True
        login_as_coach(context)
    elif "as_learner" in context.tags:
        context.logged_in = True
        login_as_learner(context)

def after_scenario(context, scenario):
    if context.logged_in:
        logout(context)

    if "download_csv" in context.tags:
        shutil.rmtree(context.download_dir)

    try:
        if hasattr(context, "sauce"):
            print("Link to your job: https://saucelabs.com/jobs/%s" % context.browser.session_id)
            if context.scenario.status == "failed":
                context.sauce.jobs.update_job(context.browser.session_id, passed=False)
            else:
                context.sauce.jobs.update_job(context.browser.session_id, passed=True)
    except Exception as e:
        if "404" in e.message:
            print("Couldn't log the job... Error message:\n" + e.message)
        else:
            raise
    finally:
        try:
            # Don't shut down the browser until all AJAX requests have completed.
            while context.browser.execute_script("return (window.jQuery || { active : 0 }).active"):
                pass
            context.browser.quit()
        except CannotSendRequest:
            pass

    database_teardown(context)

def database_setup(context):
    """
    Behave features are analogous to test suites, and behave scenarios are analogous to TestCases, but due to
    implementation details each _feature_ is wrapped in a TestCase. This and database_teardown should simulate the
    setup/teardown done by TestCases in order to achieve consistent isolation.
    """
    KALiteTestCase.setUpDatabase()

def database_teardown(context):
    """
    Behave features are analogous to test suites, and behave scenarios are analogous to TestCases, but due to
    implementation details each _feature_ is wrapped in a TestCase. This and database_setup should simulate the
    setup/teardown done by TestCases in order to achieve consistent isolation.
    """
    for alias in connections:
        call_command("flush", database=alias, interactive=False)

def do_fake_registration():
    """
    Register the device, in case some feature being tested depends on it. Will be undone by the database teardown.
    """
    # Create a Zone and DeviceZone to fool the Device into thinking it's registered
    zone = Zone(name="The Danger Zone", description="Welcome to it.")
    zone.save()
    device = Device.get_own_device()
    device_zone = DeviceZone(device=device, zone=zone)
    device_zone.save()
