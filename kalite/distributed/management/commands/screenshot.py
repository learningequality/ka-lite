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
    1. Create a separate sqlite3 database on the /data/screenshots/ folder.
    2. Read contents of screenshots from /kalite/distributed/data/screenshots.json.
    3. Save the screenshots to /data/screenshots folder.
    4. Delete the created sqlite3 database.
    """
    help = "Generate screenshots to be used on the User manual."

    def handle(self, *args, **options):
        sc = Screenshot()
        sc.snap_all()
        # since we used a new sqlite database for this command we must delete it after
        database_name = getattr(settings, 'SCREENSHOTS_DATABASE_NAME', 'data.sqlite')
        if database_name != "data.sqlite":
            delete_sqlite_database(sc.database)


# REF: http://stackoverflow.com/questions/273192/check-if-a-directory-exists-and-create-it-if-necessary
def make_sure_path_exists(path):
    """
    Check if directory exists and create it if necessary.
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
# ENDREF:


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

    database = settings.DATABASES[getattr(settings, 'SCREENSHOTS_ROUTER', 'default')]['NAME']

    def __init__(self, *args, **kwargs):

        # setup database to use and auto-create admin user
        log.info('==> Setting-up database ...')
        self.admin_user = reset_sqlite_database(self.admin_username, self.admin_email, self.default_password)
        self.admin_pass = self.default_password

        self.facility = self.create_facility()
        self.create_student(self.student_username, self.default_password, self.facility.name)
        self.create_teacher(self.coach_username, self.default_password, self.facility.name)

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
        json_keys = ['users', 'slug', 'start_url', 'inputs', 'pages', 'notes']
        try:
            values = [shot[key] for key in json_keys]
            if values:
                return True
        except Exception as exc:
            log.error("Screenshot JSON must have keys %s\n but has invalid format: \n  json==%s\n  exception==%s" %
                      (json_keys, shot, exc,))
        return False

    def make_filename(self, slug):
        make_sure_path_exists(settings.SCREENSHOTS_OUTPUT_PATH)
        filename = "%s/%s.png" % (settings.SCREENSHOTS_OUTPUT_PATH, slug,)
        return filename

    def snap(self, shot, browser=None):
        """
        Take a screenshot and save on SCREENSHOTS_OUTPUT_PATH.
        """
        start_url = '/'
        try:
            if not self.validate_json_item(shot):
                return False

            if USER_TYPE_STUDENT in shot["users"] and self.last_user is not USER_TYPE_STUDENT:
                self.browser_login_student(self.student_username, self.default_password, self.facility.name)
                self.last_user = USER_TYPE_STUDENT
            elif USER_TYPE_COACH in shot["users"] and self.last_user is not USER_TYPE_COACH:
                # MUST: `expect_success=False` is needed here to prevent this error:
                # exception:  'Screenshot' object has no attribute '_type_equality_funcs'
                self.browser_login_teacher(self.coach_username, self.default_password, self.facility.name, False)
                self.last_user = USER_TYPE_COACH
            elif USER_TYPE_ADMIN in shot["users"] and self.last_user is not USER_TYPE_ADMIN:
                self.browser_login_user(self.admin_username, self.default_password)
                self.last_user = USER_TYPE_ADMIN
            elif USER_TYPE_GUEST in shot["users"] and self.last_user is not USER_TYPE_GUEST:
                self.browser_logout_user()
                self.last_user = USER_TYPE_GUEST

            start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
            if self.browser.current_url != start_url:
                self.browse_to(start_url)

            # Make browser inputs and take screenshots as specified.
            inputs = shot["inputs"]
            for item in inputs:
                key = item.keys()[0]
                value = item.values()[0]
                if key:
                    key = key.lower()
                    if key == "<shot>":
                        filename = self.make_filename(slug=item[key])
                        self.browser.save_screenshot(filename)
                        continue
                    elif key == "<submit>":
                        self.browser_send_keys(Keys.RETURN)
                        continue
                    else:
                        if "#" in key:
                            key = key.replace("#", "")
                            self.browser_activate_element(id=key)
                        else:
                            self.browser_activate_element(name=key)
                self.browser_form_fill(value)

            if shot["slug"]:
                filename = self.make_filename(slug=shot["slug"])
                log.info('====> Snapping %s --titled-- "%s" --> %s.png ...' %
                         (self.browser.current_url, self.browser.title, shot["slug"],))
                self.browser.save_screenshot(filename)
            return True
        except Exception as exc:
            log.error("====> EXCEPTION snapping url %s: %s" % (start_url, exc,))
            return False

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
