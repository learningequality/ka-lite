import errno
import json
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.urlresolvers import reverse
from django.utils.six import StringIO

from selenium import webdriver

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

log = settings.LOG


class Command(BaseCommand):
    help = "Generate screenshots to be used on the User manual."

    def handle(self, *args, **options):
        sc = Screenshot()
        sc.snap_all()
        sc.delete_database()


# REF: http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
# ENDREF:


class Screenshot(KALiteDistributedBrowserTestCase):
    """
    Override the values from base class for better looking screenshot data.
    """
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    coach_username = 'coach'
    student_username = 'student'
    default_password = 'password'
    facility = None

    database = settings.DATABASES[settings.SCREENSHOTS_ROUTER]['NAME']

    def __init__(self, *args, **kwargs):

        # setup database to use
        log.info('==> Setting-up database ...')
        new_io = StringIO()
        call_command("reset_db", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        call_command("syncdb", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        call_command("migrate", interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)

        # create users
        log.info('==> Creating users ...')
        call_command("createsuperuser",
                     username=self.admin_username, email=self.admin_email,
                     interactive=False, stdout=new_io, router=settings.SCREENSHOTS_ROUTER)
        self.admin_user = User.objects.get(username=self.admin_username)
        self.admin_pass = self.default_password
        self.admin_user.set_password(self.admin_pass)
        self.admin_user.save()

        self.facility = self.create_facility()
        self.create_student(username=self.student_username, password=self.default_password,
                            facility_name=self.facility.name)
        self.create_teacher(username=self.coach_username, password=self.default_password,
                            facility_name=self.facility.name)

        self.persistent_browser = True
        self.max_wait_time = kwargs.get("max_wait_time", 30)

        self.setUpClass()

        # self.browser = webdriver.PhantomJS()
        log.info('==> Setting-up browser ...')
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(1024, 768)

        log.info('==> Browser %s successfully setup with live_server_url %s.' %
                 (self.browser.name, self.live_server_url,))
        log.info('==> Saving screenshots at %s ...' % (settings.SCREENSHOTS_OUTPUT_PATH,))

    def delete_database(self):
        try:
            database = settings.DATABASES[settings.SCREENSHOTS_ROUTER]['NAME']
            if os.path.exists(self.database):
                log.info('==> Removing database %s ...' % database)
                os.remove(database)
                log.info('====> Successfully removed database.')
        except Exception as exc:
            log.error('====> EXCEPTION: %s' % exc)
            pass

    def get_contents(self):
        """
        Get the contents of shots.
        """
        items = []
        try:
            log.info('==> Fetching list of screenshots from %s ...' % (settings.SCREENSHOTS_JSON_FILE,))
            items = json.load(open(settings.SCREENSHOTS_JSON_FILE))
        except Exception as exc:
            log.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" %
                      (settings.SCREENSHOTS_JSON_FILE, exc,))
        return items

    def validate_json_item(self, shot):
        """
        Validates a json item if keys are valid or not.
        """
        try:
            values = [shot[key] for key in settings.SCREENSHOTS_JSON_KEYS]
            if values:
                return True
        except Exception as exc:
            log.error("Screenshot JSON has invalid format: \n  json==%s\n  exception==%s" % (shot, exc,))
        return False

    def make_filename(self, slug):
        make_sure_path_exists(settings.SCREENSHOTS_OUTPUT_PATH)
        filename = "%s/%s.png" % (settings.SCREENSHOTS_OUTPUT_PATH, slug,)
        return filename

    def snap(self, shot, browser=None):
        """
        Take a screenshot and save on SCREENSHOTS_OUTPUT_PATH.
        """
        if not self.validate_json_item(shot):
            return False

        if USER_TYPE_STUDENT in shot["users"]:
            self.browser_login_student(username=self.student_username, password=self.default_password)
        elif USER_TYPE_COACH in shot["users"]:
            # MUST: `expect_success=False` is needed here to prevent this error:
            # exception:  'Screenshot' object has no attribute '_type_equality_funcs'
            self.browser_login_teacher(username=self.coach_username, password=self.default_password,
                                       expect_success=False)
        elif USER_TYPE_ADMIN in shot["users"]:
            self.browser_login_user(self.admin_username, self.default_password)
        elif USER_TYPE_GUEST in shot["users"]:
            self.browser_logout_user()

        start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
        self.browse_to(start_url)

        # TODO(cpauya): take actions to get to the `end_url`
        # TODO(cpauya): wait until we are at `end_url`

        filename = self.make_filename(slug=shot["slug"])
        log.info('====> Snapping %s --titled-- "%s" --> %s.png ...' %
                 (self.browser.current_url, self.browser.title, shot["slug"],))
        self.browser.save_screenshot(filename)
        return True

    def snap_all(self, browser=None):
        """
        Take screenshots for each item from json grouped by user.
        """
        shots = []
        try:
            log.info('==> Fetching screenshots.json from %s ...' % (settings.SCREENSHOTS_JSON_FILE,))
            shots = json.load(open(settings.SCREENSHOTS_JSON_FILE))
            for shot in shots:
                self.snap(shot, browser=browser)
            self.browser.quit()
        except Exception as exc:
            log.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" %
                      (settings.SCREENSHOTS_JSON_FILE, exc,))
