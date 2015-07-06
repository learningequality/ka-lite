import glob
import json
import os

from optparse import make_option
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.utils.six import StringIO

from securesync.models import Device, DeviceZone, Zone

from fle_utils.general import ensure_dir
from kalite.testing.base import KALiteBrowserTestCase
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.browser_mixins import BrowserActionMixins
from kalite.distributed.management.commands.katest import unregister_distributed_server
from kalite.facility.models import Facility

USER_TYPE_ADMIN = "admin"
USER_TYPE_COACH = "coach"
USER_TYPE_GUEST = "guest"
USER_TYPE_STUDENT = "learner"

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

    option_list = BaseCommand.option_list + (
        make_option('--from-str',
            action='store',
            dest='cl_str',
            default=None,
            help='Takes a JSON string instead of reading from the default file location.'),
        make_option('--output-dir',
            action='store',
            dest='output_dir',
            default=None,
            help='Specify the output directory relative to the project base directory.'),
        make_option('--no-del',
            action='store_true',
            dest='no_del',
            default=None,
            help='Don\'t delete existing screenshots.'),
        make_option('--lang',
            action='store',
            dest='language',
            default=None,
            help='Specify the language of the session, set by the "set_default_language" api endpoint.'),
        )

    def handle(self, *args, **options):
        sc = Screenshot(**options)
        sc.snap_all(**options)
        # since we used a new sqlite database for this command we must delete it after
        database_name = getattr(settings, 'SCREENSHOTS_DATABASE_NAME', None)
        if database_name:
            delete_sqlite_database(sc.database, verbosity=options['verbosity'])


# Possibly re-usable codes.
def reset_sqlite_database(username=None, email=None, password=None, router=None, verbosity="1"):
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
        call_command("syncdb", interactive=False, stdout=new_io, router=router, verbosity=verbosity)
        call_command("syncdb", interactive=False, stdout=new_io, router=router, verbosity=verbosity, database="assessment_items")
        call_command("migrate", interactive=False, stdout=new_io, router=router, verbosity=verbosity)
        call_command("generaterealdata", interactive=False, stdout=new_io, router=router, verbosity=verbosity)  # For coachreports pages
        if username and email and password:
            log.info('==> Creating superuser username==%s; email==%s ...' % (username, email,)) if int(verbosity) > 0 else None
            call_command("createsuperuser", username=username, email=email,
                         interactive=False, stdout=new_io, router=router, verbosity=verbosity)
            admin_user = User.objects.get(username=username)
            admin_user.set_password(password)
            admin_user.save()
            return admin_user
    return None


def delete_sqlite_database(database=None, verbosity="1"):
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
                log.info('==> Removing database %s ...' % database) if int(verbosity) > 0 else None
                os.remove(database)
                log.info('====> Successfully removed database.') if int(verbosity) > 0 else None
    except Exception as exc:
        log.error('====> EXCEPTION: %s' % exc)


class Screenshot(FacilityMixins, BrowserActionMixins, KALiteBrowserTestCase):
    """
    Override the values from base class for better looking screenshot data.
    """
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    coach_username = 'coach'
    student_username = 'student'
    default_password = 'password'
    facility = None

    KEY_USERS = 'users'
    KEY_SLUG = 'slug'
    KEY_START_URL = 'start_url'
    KEY_INPUTS = 'inputs'
    KEY_PAGES = 'pages'
    KEY_FOCUS = 'focus'
    KEY_NOTES = 'notes'

    KEY_CMD_SLUG = '<slug>'
    KEY_CMD_SUBMIT = '<submit>'

    JSON_KEYS = (KEY_USERS, KEY_SLUG, KEY_START_URL, KEY_INPUTS, KEY_PAGES, KEY_NOTES,)

    database = getattr(settings, 'SCREENSHOTS_DATABASE_PATH', None)

    verbosity = 1
    output_path = None

    def _fake_test():
        # Fools django.utils.unittest.case.TestCase.__init__
        # See the small novel comment under __init__ below
        pass

    def logwarn(self, *args, **kwargs):
        if int(self.verbosity) > 0:
            log.warn(*args, **kwargs)

    def loginfo(self, *args, **kwargs):
        if int(self.verbosity) > 0:
            log.info(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        # It's not good to override __init__ for classes that inherit from TestCase
        # Since we're hackily inheriting here, we have to hackily invoke __init__
        # Perhaps better would be to decouple this class from the testing framework
        # by ditching the various mixins (they invoke TestCase methods) and just calling
        # selenium methods directly, as the mixins are a thin wrapper for that.
        # -- M.C. Gallaspy, 1/21/2015
        KALiteBrowserTestCase.__init__(self, "_fake_test")

        self.verbosity = kwargs['verbosity']

        # make sure output path exists and is empty
        if kwargs['output_dir']:
            self.output_path = os.path.join( os.path.realpath(os.path.join(settings.PROJECT_PATH, '..')),
                                        kwargs['output_dir'])
        else:
            self.output_path = settings.SCREENSHOTS_OUTPUT_PATH
        ensure_dir(self.output_path)

        # make sure directory is empty from screenshot files
        png_path = os.path.join(self.output_path, "*%s" % settings.SCREENSHOTS_EXTENSION)
        pngs = glob.glob(png_path)
        if pngs and not kwargs['no_del']:
            self.logwarn("==> Deleting existing screenshots: %s ..." % png_path)
            for filename in pngs:
                os.remove(filename)

        # setup database to use and auto-create admin user
        self.loginfo("==> Setting-up database ...")
        self.admin_user = reset_sqlite_database(self.admin_username, self.admin_email, self.default_password, verbosity=self.verbosity)
        self.admin_pass = self.default_password
        if not self.admin_user:
            raise Exception("==> Did not successfully setup database!")

        Facility.initialize_default_facility("Silly Facility")  # Default facility required to avoid pernicious facility selection page
        facility = self.facility = Facility.objects.get(name="Silly Facility")
        self.create_student(username=self.student_username, password=self.default_password, facility=facility)
        self.create_teacher(username=self.coach_username, password=self.default_password, facility=facility)

        self.persistent_browser = True
        self.max_wait_time = kwargs.get('max_wait_time', 30)

        self.setUpClass()

        self.loginfo("==> Setting-up browser ...")
        super(Screenshot, self).setUp()
        # Selenium won't scroll to an element, so we have to make the window size is large enough so that everything is visible
        self.browser.set_window_size(1024, 768)
        # self.browser.implicitly_wait(3)

        # After initializing the server (with setUp) and a browser, set the language
        self.set_session_language(kwargs['language'])

        self.loginfo("==> Browser %s successfully setup with live_server_url %s." %
                 (self.browser.name, self.live_server_url,))
        self.loginfo("==> Saving screenshots to %s ..." % (settings.SCREENSHOTS_OUTPUT_PATH,))

    def set_session_language(self, lang_code):
        """ Uses the "set_default_language" api endpoint to set the language for the session.
        The language pack should already be downloaded, or the behavior is undefined.
        TODO: Handle the case when the language pack is not downloaded.

        :param lang_code: A string with the language code or None. Value None is a no-op 
        """
        if not lang_code:
            return
        self.browser.get(self.live_server_url + reverse("homepage"))
        self.browser_wait_for_js_object_exists("$")
        data = json.dumps({"lang": lang_code})
        self.browser.execute_script("window.SUCCESS=false; $.ajax({type: \"POST\", url: \"%s\", data: '%s', contentType: \"application/json\", success: function(){window.SUCCESS=true}})" % (reverse("set_default_language"), data))
        self.browser_wait_for_js_condition("window.SUCCESS")    
        # Ensure the changes are loaded 
        self.browser.get(self.live_server_url + reverse("homepage"))

    def validate_json_keys(self, shot):
        """
        Validates a json item if keys are valid or not, raises an exception if keys are found.
        """
        values = [shot[key] for key in self.JSON_KEYS]

    def make_filename(self, slug):
        filename = "%s/%s%s" % (self.output_path, slug, settings.SCREENSHOTS_EXTENSION)
        return filename

    def snap(self, slug, focus, note):
        filename = self.make_filename(slug=slug)
        self.loginfo('====> Snapping %s --titled-- "%s" --> %s%s ...' %
                 (self.browser.current_url, self.browser.title, slug, settings.SCREENSHOTS_EXTENSION))

        if focus:
            self.browser_wait_for_js_object_exists("$")
            selector = focus['selector']
            styles = focus['styles']
            try:
                for key, value in styles.iteritems():
                    self.browser.execute_script('$("%s").css("%s", "%s");' % (selector, key, value))
                if note:
                    self.browser.execute_script("$('%s').qtip({content:{text:\"%s\"},show:{ready:true,delay:0,effect:false}})" % (selector, note))
            except WebDriverException as e:
                log.error("Error taking screenshot:")
                log.error(str(e))
                log.error("Screenshot info: {0}".format((focus, note)))
                log.error("Current url: {0}".format(self.browser.current_url))
                import sys
                sys.exit(1)
        self.browser.save_screenshot(filename)

    def process_snap(self, shot, browser=None):
        """
        Take a screenshot and save on SCREENSHOTS_OUTPUT_PATH.
        """
        self.validate_json_keys(shot)

        start_url = '/'
        # Let's just always start logged out
        if self.browser_is_logged_in():
            self.browser_logout_user()

        # Make sure to unregister after finishing for the next shot
        if shot["registered"]:
            self._do_fake_registration()

        if USER_TYPE_STUDENT in shot[self.KEY_USERS] and not self.browser_is_logged_in(self.student_username):
            self.browser_login_student(self.student_username, self.default_password, self.facility.name)
        elif USER_TYPE_COACH in shot[self.KEY_USERS] and not self.browser_is_logged_in(self.coach_username):
            self.browser_login_teacher(self.coach_username, self.default_password, self.facility.name)
        elif USER_TYPE_ADMIN in shot[self.KEY_USERS] and not self.browser_is_logged_in(self.admin_username):
            self.browser_login_user(self.admin_username, self.default_password)
        elif USER_TYPE_GUEST in shot[self.KEY_USERS] and self.browser_is_logged_in():
            self.browser_logout_user()

        start_url = "%s%s" % (self.live_server_url, shot["start_url"],)
        if self.browser.current_url != start_url:
            self.browse_to(start_url)

        inputs = shot[self.KEY_INPUTS]
        focus = shot[self.KEY_FOCUS] if self.KEY_FOCUS in shot else {}
        note = shot[self.KEY_NOTES] if self.KEY_NOTES in shot else {}
        for item in inputs:
            for key, value in item.iteritems():
                if key:
                    if key.lower() == self.KEY_CMD_SLUG:
                        self.snap(slug=value, focus=focus, note=note)
                    elif key.lower() == self.KEY_CMD_SUBMIT:
                        self.browser_send_keys(Keys.RETURN)
                    else:
                        if key[0] == "#":
                            kwargs = {'id': key[1:]}
                        elif key[0] == ".":
                            kwargs = {'css_class': key[1:]}
                        else:
                            kwargs = {'name': key}
                        self.browser_activate_element(**kwargs)
                        if value:
                            self.browser_send_keys(value)
                elif not key and value:
                    self.browser_send_keys(value)

        if shot[self.KEY_SLUG]:
            self.snap(slug=shot[self.KEY_SLUG], focus=focus, note=note)

        if shot["registered"]:
            self._undo_fake_registration()

    def snap_all(self, browser=None, **options):
        """
        Take screenshots for each item from json grouped by user.
        """
        shots = []
        if options['cl_str']:
            shots = json.loads(options['cl_str'])
        else:
            self.loginfo('==> Fetching screenshots.json from %s ...' % (settings.SCREENSHOTS_JSON_FILE,))
            shots = json.load(open(settings.SCREENSHOTS_JSON_FILE))
        for shot in shots:
            self.process_snap(shot, browser=browser)
        self.browser.quit()

    def _do_fake_registration(self):
        # Create a Zone and DeviceZone to fool the Device into thinking it's registered
        zone = Zone(name="The Danger Zone", description="Welcome to it.")
        zone.save()
        device = Device.get_own_device()
        deviceZone = DeviceZone(device=device, zone=zone)
        deviceZone.save()
    
    def _undo_fake_registration(self):
        unregister_distributed_server()
