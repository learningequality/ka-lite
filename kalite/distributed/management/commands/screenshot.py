import errno
import json
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from kalite.testing.browser import browse_to
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase


try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = object()

SCREENSHOT_PATH = os.path.join(os.path.realpath(getattr(local_settings, "PROJECT_PATH", settings.PROJECT_PATH)),
                               "..", "data", "screenshots")
SCREENSHOT_KEYS = ['users', 'slug', 'start_url', 'inputs', 'end_url']
SCREENSHOT_JSON_FILE = os.path.join(settings.SCREENSHOTS_DATA_PATH, 'screenshots.json')

USER_TYPE_ADMIN = "admin"
USER_TYPE_COACH = "coach"
USER_TYPE_GUEST = "guest"
USER_TYPE_STUDENT = "student"

ADMIN_USERNAME = 'cy'
ADMIN_PASSWORD = 'cy'
COACH_USERNAME = 'coach'
COACH_PASSWORD = 'password'
STUDENT_USERNAME = 'student'
STUDENT_PASSWORD = 'password'


class Command(BaseCommand):
    help = "Generate screenshots to be used on the User manual."

    def handle(self, *args, **options):
        sc = Screenshot()
        sc.take_all()


# REF: http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
# ENDREF:


class Screenshot(KALiteDistributedBrowserTestCase):
# class Screenshot():
    logging.warn('==> screenshot %s' % (SCREENSHOT_PATH,))

    def __init__(self, *args, **kwargs):

        # super(Screenshot, self).__init__(*args, **kwargs)
        self.persistent_browser = True
        self.max_wait_time = kwargs.get("max_wait_time", 30)
        # self.admin_user = User.objects.filter(is_superuser=True, is_active=True)[0]
        self.admin_user = User.objects.filter(username=ADMIN_USERNAME, is_superuser=True, is_active=True)[0]
        self.admin_pass = ADMIN_PASSWORD
        self.setUpClass()
        self.create_facility()
        self.create_student()
        self.create_teacher()

        # self.browser = webdriver.PhantomJS()
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(1024, 768)

        # self.browser_login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
        self.browser_login_admin()
        filename = self.make_filename(slug="admin-home")
        self.browser.save_screenshot(filename)
        logging.warn('==> live_server_url %s' % (self.live_server_url,))

    def get_contents(self):
        """
        Get the contents of shots.
        """
        items = []
        try:
            items = json.load(open(SCREENSHOT_JSON_FILE))
        except Exception as exc:
            logging.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" % (SCREENSHOT_JSON_FILE, exc,))
        return items

    def validate_json_item(self, shot, auto_login=True):
        """
        Validates a json item if keys are valid or not.
        """
        try:
            values = [shot[key] for key in SCREENSHOT_KEYS]
            if values:
                if auto_login:
                    if USER_TYPE_ADMIN in shot["users"]:
                        self.browser_login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
                return True
        except Exception as exc:
            logging.error("Screenshot JSON has invalid format: \n  json==%s\n  exception==%s" % (shot, exc,))
        return False

    def make_filename(self, slug):
        make_sure_path_exists(SCREENSHOT_PATH)
        filename = "%s/%s.png" % (SCREENSHOT_PATH, slug,)
        return filename

    def take(self, shot, browser=None):
        """
        Take screenshot and save on SCREENSHOT_PATH.
        """
        start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
        # start_url = "%s%s" % ('', shot["start_url"],)
        self.browse_to(start_url)

        # logging.warn('==> current_url %s' % (self.browser.current_url,))

        # TODO(cpauya): take actions to get to the `end_url`
        # TODO(cpauya): wait until we are at `end_url`

        # make_sure_path_exists(SCREENSHOT_PATH)
        # filename = "%s/%s.png" % (SCREENSHOT_PATH, shot["slug"],)
        filename = self.make_filename(slug=shot["slug"])
        logging.warn('==> screenshot %s -- %s -- %s' % (filename, self.browser.current_url, self.browser.title,))
        self.browser.save_screenshot(filename)

    def take_all(self, browser=None):
        """
        Take screenshots for each item from json.
        """
        shots = self.get_contents()
        for shot in shots:
            if not self.validate_json_item(shot):
                continue
            self.take(shot, browser=browser)
        self.browser.quit()