import errno
import json
import logging
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from selenium import webdriver


try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = object()

SCREENSHOT_PATH = os.path.join(os.path.realpath(getattr(local_settings, "PROJECT_PATH", settings.PROJECT_PATH)),
                               "..", "data", "screenshots")
SCREENSHOT_KEYS = ['user_types', 'slug', 'start_url', 'inputs', 'end_url']
SCREENSHOT_JSON_FILE = os.path.join(os.path.dirname(__file__), 'screenshots.json')
SCREENSHOT_URL = "http://127.0.0.1:8008"


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


class Screenshot():
    logging.warn('==> screenshot %s' % (SCREENSHOT_PATH,))

    def __init__(self, *args, **kwargs):
        # TODO(cpauya): Firefox driver is throwing an exception
        # TODO: Firefox driver is throwing an exception
        # self.browser = webdriver.Firefox()
        # self.browser.set_screen_size(1024, 768)
        self.browser = webdriver.PhantomJS()

    def get_json_contents(self):
        """
        Get the .json content.
        """
        logging.warn('==> %s' % ('get_json_contents',))
        items = []
        try:
            items = json.load(open(SCREENSHOT_JSON_FILE))
        except Exception as exc:
            logging.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" % (SCREENSHOT_JSON_FILE, exc,))
        return items

    def validate_json_item(self, shot):
        """
        Validates a json item if keys are valid or not.
        """
        try:
            values = [shot[key] for key in SCREENSHOT_KEYS]
            if values:
                return True
        except Exception as exc:
            logging.error("Screenshot JSON has invalid format: \n  json==%s\n  exception==%s" % (shot, exc,))
        return False

    def take(self, item, browser=None):
        """
        Take screenshot and save on SCREENSHOT_PATH.
        """
        filename = "%s.png" % (item["slug"],)
        start_url = "%s%s" % (SCREENSHOT_URL, item["start_url"],)
        self.browser.get(start_url)

        # TODO(cpauya): take actions to get to the `end_url`
        # TODO(cpauya): wait until we are at `end_url`

        make_sure_path_exists(SCREENSHOT_PATH)
        filename = "%s/%s.png" % (SCREENSHOT_PATH, item["slug"],)
        logging.warn('==> screenshot %s -- %s -- %s' % (filename, self.browser.current_url, self.browser.title,))
        self.browser.save_screenshot(filename)

    def take_all(self, browser=None):
        """
        Take screenshots for each item from json.
        """
        logging.warn('==> take_all')
        items = self.get_json_contents()
        for item in items:
            if not self.validate_json_item(item):
                continue
            # logging.warn('====> json item %s' % item)
            self.take(item, browser=browser)
        self.browser.quit()