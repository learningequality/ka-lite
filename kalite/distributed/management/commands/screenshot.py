import errno
import json
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.utils.six import StringIO

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from kalite.testing.browser import browse_to
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase


try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = object()

USER_TYPE_ADMIN = "admin"
USER_TYPE_COACH = "coach"
USER_TYPE_GUEST = "guest"
USER_TYPE_STUDENT = "student"

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'
ADMIN_EMAIL = 'admin@example.com'
COACH_USERNAME = 'coach'
COACH_PASSWORD = 'password'
STUDENT_USERNAME = 'student'
STUDENT_PASSWORD = 'password'

log = settings.LOG


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
    # log.info('==> screenshot %s' % (SCREENSHOTS_OUTPUT_PATH,))

    def __init__(self, *args, **kwargs):

        new_io = StringIO()
        call_command("reset_db", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        # command_output = new_io.getvalue().strip()
        call_command("syncdb", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        call_command("migrate", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        call_command("createsuperuser",
                     username=ADMIN_USERNAME, email=ADMIN_EMAIL,
                     interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        u = User.objects.get(username=ADMIN_USERNAME)
        u.set_password(ADMIN_PASSWORD)
        u.save()

        self.persistent_browser = True
        self.max_wait_time = kwargs.get("max_wait_time", 30)
        # self.admin_user = User.objects.filter(is_superuser=True, is_active=True)[0]
        admins = User.objects.filter(username=ADMIN_USERNAME, is_superuser=True, is_active=True)
        if not admins:
            raise CommandError("No super user found!")
        self.admin_user = admins[0]
        self.admin_pass = ADMIN_PASSWORD
        self.setUpClass()

        self.create_facility()
        self.create_student()
        self.create_teacher()

        # self.browser = webdriver.PhantomJS()
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(1024, 768)

        log.info('==> live_server_url %s' % (self.live_server_url,))
        log.info('==> Saving screenshots at %s ...' % (settings.SCREENSHOTS_OUTPUT_PATH,))

    def get_contents(self):
        """
        Get the contents of shots.
        """
        items = []
        try:
            log.info('==> Fetching screenshots.json from %s ...' % (settings.SCREENSHOTS_JSON_FILE,))
            items = json.load(open(settings.SCREENSHOTS_JSON_FILE))
        except Exception as exc:
            log.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" %
                      (settings.SCREENSHOTS_JSON_FILE, exc,))
        return items

    def validate_json_item(self, shot, auto_login=True):
        """
        Validates a json item if keys are valid or not.
        """
        try:
            values = [shot[key] for key in settings.SCREENSHOTS_JSON_KEYS]
            if values:
                if auto_login:
                    if USER_TYPE_STUDENT in shot["users"]:
                        self.browser_login_student()
                    elif USER_TYPE_COACH in shot["users"]:
                        self.browser_login_teacher()
                    elif USER_TYPE_ADMIN in shot["users"]:
                        self.browser_login_user(ADMIN_USERNAME, ADMIN_PASSWORD)
                return True
        except Exception as exc:
            log.error("Screenshot JSON has invalid format: \n  json==%s\n  exception==%s" % (shot, exc,))
        return False

    def make_filename(self, slug):
        make_sure_path_exists(settings.SCREENSHOTS_OUTPUT_PATH)
        filename = "%s/%s.png" % (settings.SCREENSHOTS_OUTPUT_PATH, slug,)
        return filename

    def take(self, shot, browser=None):
        """
        Take screenshot and save on SCREENSHOTS_OUTPUT_PATH.
        """
        start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
        # start_url = "%s%s" % ('', shot["start_url"],)
        self.browse_to(start_url)

        # TODO(cpauya): take actions to get to the `end_url`
        # TODO(cpauya): wait until we are at `end_url`

        filename = self.make_filename(slug=shot["slug"])
        log.info('==> %s --titled-- "%s" --> %s.png ...' %
                 (self.browser.current_url, self.browser.title, shot["slug"],))
        self.browser.save_screenshot(filename)

    def take_all(self, browser=None):
        """
        Take screenshots for each item from json grouped by user.
        """
        shots = self.get_contents()
        for shot in shots:
            if not self.validate_json_item(shot):
                continue
            self.take(shot, browser=browser)
        self.browser.quit()