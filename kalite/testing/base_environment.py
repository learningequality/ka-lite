"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.
"""
import tempfile
import shutil

from behave import *
from httplib import CannotSendRequest
from selenium import webdriver
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

# FYI: scenario tags are inherited from features, so tagging a feature is almost the same as tagging each
# scenario individually, as long as you are cautious not to duplicate logic in before_feature and before_scenario.
def before_scenario(context, scenario):
    database_setup(context)

    if "registered_device" in context.tags:
        do_fake_registration()

    profile = webdriver.FirefoxProfile()
    if "download_csv" in context.tags:
        # Let csv files be downloaded automatically. Can be accessed using context.download_dir
        context.download_dir = tempfile.mkdtemp()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", context.download_dir)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")

    browser = context.browser = webdriver.Firefox(firefox_profile=profile)
    # ensure the window is reasonably sized.
    browser.set_window_size(2560, 1920)

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