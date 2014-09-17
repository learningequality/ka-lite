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
from selenium.webdriver.common.keys import Keys

from fle_utils.general import ensure_dir

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
    """
    This will generate screenshots based on the selenium firefox webdriver to be used for the user guide document.
    1. Sets output of database and screenshots to /data/screenshots/ folder.
    2. Create a separate sqlite3 database on the output folder.
    3. Delete any .png files from the output folder.
    4. Read contents of screenshots from /kalite/distributed/data/screenshots.json.
    5. Save the screenshots to the output folder.
    6. Delete the created sqlite3 database.
    """
    help = "Generate screenshots to be used on the User manual."

    def handle(self, *args, **options):
        sc = Screenshot()
        sc.snap_all()
        # since we used a new sqlite database for this command we must delete it after
        database_name = getattr(settings, 'SCREENSHOTS_DATABASE_NAME', None)
        if database_name:
            delete_sqlite_database(sc.database)


# Possibly re-usable codes.
def reset_sqlite_database(username=None, email=None, password=None, router=None):
    """
    Resets the currently used sqlite database.  Creates the user if admin_username is passed.
    :param username: If present, creates a superuser with this username.
    :param email: If present, creates a superuser with this email.
    :param password: If present, creates a superuser with this password.
    :param router: The database router to use.
    :return: Returns the superuser created or None if no arguments are provided.
    """
    if not router:
        router = getattr(settings, 'SCREENSHOTS_ROUTER', 'default')
    db_engine = settings.DATABASES[router]['ENGINE']
    if db_engine == settings.SQLITE3_ENGINE:

        # make sure database path exists
        ensure_dir(settings.SCREENSHOTS_OUTPUT_PATH)

        new_io = StringIO()
        call_command("reset_db", interactive=False, stdout=new_io, router=router)
        call_command("syncdb", interactive=False, stdout=new_io, router=router)
        call_command("migrate", interactive=False, stdout=new_io, router=router)
        if username and email and password:
            log.info('==> Creating superuser username==%s; email==%s ...' % (username, email,))
            call_command("createsuperuser", username=username, email=email,
                         interactive=False, stdout=new_io, router=router)
            admin_user = User.objects.get(username=username)
            admin_user.set_password(password)
            admin_user.save()
            return admin_user
    return None


def delete_sqlite_database(database=None):
    """
    Delete the specified sqlite database or if None, the one on `settings.py` of the app or project.
    :param database: The database filename with full path.
    """
    try:
        router = getattr(settings, 'SCREENSHOTS_ROUTER', 'default')
        db_engine = settings.DATABASES[router]['ENGINE']
        if db_engine == settings.SQLITE3_ENGINE:
            if not database:
                database = settings.DATABASES[router]['NAME']
            if os.path.exists(database):
                log.info('==> Removing database %s ...' % database)
                os.remove(database)
                log.info('====> Successfully removed database.')
    except Exception as exc:
        log.error('====> EXCEPTION: %s' % exc)


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
    last_user = USER_TYPE_GUEST

    KEY_USERS = 'users'
    KEY_SLUG = 'slug'
    KEY_START_URL = 'start_url'
    KEY_INPUTS = 'inputs'
    KEY_PAGES = 'pages'
    KEY_NOTES = 'notes'

    KEY_CMD_SLUG = '<slug>'
    KEY_CMD_SUBMIT = '<submit>'

    JSON_KEYS = (KEY_USERS, KEY_SLUG, KEY_START_URL, KEY_INPUTS, KEY_PAGES, KEY_NOTES,)

    database = getattr(settings, 'SCREENSHOTS_DATABASE_PATH', None)

    def __init__(self, *args, **kwargs):

        # make sure output path exists and is empty
        output_path = settings.SCREENSHOTS_OUTPUT_PATH
        ensure_dir(output_path)

        # make sure directory is empty from screenshot files
        import glob
        png_path = os.path.join(output_path, "*%s" % settings.SCREENSHOTS_EXTENSION)
        pngs = glob.glob(png_path)
        if pngs:
            log.warn("==> Deleting existing screenshots: %s ..." % png_path)
            for filename in pngs:
                os.remove(filename)

        # setup database to use and auto-create admin user
        log.info("==> Setting-up database ...")
        self.admin_user = reset_sqlite_database(self.admin_username, self.admin_email, self.default_password)
        self.admin_pass = self.default_password
        if not self.admin_user:
            raise Exception("==> Did not successfully setup database!")

        self.facility = self.create_facility()
        self.create_student(self.student_username, self.default_password, self.facility.name)
        self.create_teacher(self.coach_username, self.default_password, self.facility.name)

        self.persistent_browser = True
        self.max_wait_time = kwargs.get('max_wait_time', 30)

        self.setUpClass()

        # self.browser = webdriver.PhantomJS()
        log.info("==> Setting-up browser ...")
        self.browser = webdriver.Firefox()
        self.browser.set_window_size(1024, 768)

        log.info("==> Browser %s successfully setup with live_server_url %s." %
                 (self.browser.name, self.live_server_url,))
        log.info("==> Saving screenshots to %s ..." % (settings.SCREENSHOTS_OUTPUT_PATH,))

    def validate_json_keys(self, shot):
        """
        Validates a json item if keys are valid or not, raises an exception if keys are found.
        """
        values = [shot[key] for key in self.JSON_KEYS]

    def make_filename(self, slug):
        ensure_dir(settings.SCREENSHOTS_OUTPUT_PATH)
        filename = "%s/%s%s" % (settings.SCREENSHOTS_OUTPUT_PATH, slug, settings.SCREENSHOTS_EXTENSION)
        return filename

    def snap(self, slug):
        filename = self.make_filename(slug=slug)
        log.info('====> Snapping %s --titled-- "%s" --> %s%s ...' %
                 (self.browser.current_url, self.browser.title, slug, settings.SCREENSHOTS_EXTENSION))
        self.browser.save_screenshot(filename)

    def process_snap(self, shot, browser=None):
        """
        Take a screenshot and save on SCREENSHOTS_OUTPUT_PATH.
        """
        self.validate_json_keys(shot)

        start_url = '/'
        try:
            if USER_TYPE_STUDENT in shot[self.KEY_USERS] and self.last_user is not USER_TYPE_STUDENT:
                self.browser_login_student(self.student_username, self.default_password, self.facility.name)
                self.last_user = USER_TYPE_STUDENT
            elif USER_TYPE_COACH in shot[self.KEY_USERS] and self.last_user is not USER_TYPE_COACH:
                # MUST: `expect_success=False` is needed here to prevent this error:
                # exception:  'Screenshot' object has no attribute '_type_equality_funcs'
                self.browser_login_teacher(self.coach_username, self.default_password, self.facility.name, False)
                self.last_user = USER_TYPE_COACH
            elif USER_TYPE_ADMIN in shot[self.KEY_USERS] and self.last_user is not USER_TYPE_ADMIN:
                self.browser_login_user(self.admin_username, self.default_password)
                self.last_user = USER_TYPE_ADMIN
            elif USER_TYPE_GUEST in shot[self.KEY_USERS] and self.last_user is not USER_TYPE_GUEST:
                self.browser_logout_user()
                self.last_user = USER_TYPE_GUEST

            start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
            if self.browser.current_url != start_url:
                self.browse_to(start_url)

            # Make browser inputs and take screenshots as specified.
            inputs = shot[self.KEY_INPUTS]
            for item in inputs:
                for key, value in item.iteritems():
                    if key:
                        if key.lower() == self.KEY_CMD_SLUG:
                            self.snap(slug=value)
                            continue
                        elif key.lower() == self.KEY_CMD_SUBMIT:
                            self.browser_send_keys(Keys.RETURN)
                            continue
                        else:
                            kwargs = {'name': key}
                            if key[0] == "#":
                                kwargs = {'id': key.replace("#", "")}
                            self.browser_activate_element(**kwargs)
                    self.browser_form_fill(value)

            if shot[self.KEY_SLUG]:
                self.snap(slug=shot[self.KEY_SLUG])
        except Exception as exc:
            log.error("====> EXCEPTION snapping url %s: %s" % (start_url, exc,))
            raise

    def snap_all(self, browser=None):
        """
        Take screenshots for each item from json grouped by user.
        """
        shots = []
        try:
            log.info('==> Fetching screenshots.json from %s ...' % (settings.SCREENSHOTS_JSON_FILE,))
            shots = json.load(open(settings.SCREENSHOTS_JSON_FILE))
            for shot in shots:
                self.process_snap(shot, browser=browser)
            self.browser.quit()
        except Exception as exc:
            log.error("Cannot open `screenshots.json` at %s:\n  exception:  %s" %
                      (settings.SCREENSHOTS_JSON_FILE, exc,))
