"""
Setup KA Lite:

 - Initialize database contents
 - Run migrations
 - Find and relocate obsolete user and data files
 - if interactive:
     - Download and unpack the english content pack, containing assessment items
     - Create super user account
     - Run 'kalite start'
"""
import getpass
import logging
import os
import re
import shutil
import sys
import tempfile
import subprocess

from distutils import spawn
from annoying.functions import get_object_or_None
from optparse import make_option
from peewee import OperationalError

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import kalite
from kalite.facility.models import Facility
from kalite.version import VERSION, SHORTVERSION
from kalite.i18n.base import CONTENT_PACK_URL_TEMPLATE, reset_content_db

from fle_utils.config.models import Settings
from fle_utils.general import get_host_name, ensure_dir
from fle_utils.platforms import is_windows
from securesync.models import Device

CONTENTPACK_URL = CONTENT_PACK_URL_TEMPLATE.format(
    version=SHORTVERSION, langcode="en", suffix="")

PRESEED_DIR = os.path.join(kalite.ROOT_DATA_PATH, "preseed")

# Examples:
# contentpack.en.zip
# contentpack-0.16.en.zip
PRESEED_CONTENT_PACK_MASK = re.compile(r"contentpack.*\.(?P<lang>[a-z]{2,}).zip")


logger = logging.getLogger(__name__)


def raw_input_yn(prompt):
    ans = ""
    while True:
        ans = raw_input("%s (yes or no) " % prompt.strip()).lower()
        if ans in ["yes", "no"]:
            break
        logger.warning("Please answer yes or no.\n")
    return ans == "yes"


def raw_input_password():
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            logger.error("\tError: password must not be blank.\n")
            continue

        elif password != getpass.getpass("Password (again): "):
            logger.error("\tError: passwords did not match.\n")
            continue
        break
    return password


def validate_username(username):
    return bool(username and (not re.match(r'^[^a-zA-Z]', username) and not re.match(r'^.*[^a-zA-Z0-9_]+.*$', username)))


def get_clean_default_username():
    username = (getpass.getuser() or "").replace("-", "_")
    # Make sure auto-username doesn't have illegal characters
    username = re.sub(r"\W", r"", username)
    # Cut off non-alphabetic leading characters
    return re.sub(r"^([^a-zA-Z])+", r"", username)


def get_username(username):
    while not validate_username(username):

        username = raw_input("Username (leave blank to use '%s'): " %
                             get_clean_default_username()) or get_clean_default_username()
        if not validate_username(username):
            logger.error(
                "\tError: Username must contain only letters, digits, and underscores, and start with a letter.\n")

    return username


def get_username_password(current_user="", password=None):
    return (get_username(current_user), password or raw_input_password())


def get_hostname_and_description(hostname=None, description=None):
    default_hostname = get_host_name()
    while not hostname:
        prompt = "Please enter a hostname for this server%s: " % (
            "" if not default_hostname else (" (or, press Enter to use '%s')" % get_host_name()))
        hostname = raw_input(prompt) or default_hostname
        if not hostname:
            logger.error("\tError: hostname must not be empty.\n")
        else:
            break

    description = description or raw_input(
        "Please enter a one-line description for this server (or, press Enter to leave blank): ")

    return (hostname, description)


def get_assessment_items_filename():
    def validate_filename(filename):
        try:
            open(filename, "r").close()
            return True
        except IOError:
            return False

    def find_recommended_file():
        filename_guess = "en.zip"
        curdir = os.path.abspath(os.curdir)
        pardir = os.path.abspath(os.path.join(curdir, os.pardir))
        while curdir != pardir:
            recommended = os.path.join(curdir, filename_guess)
            if os.path.exists(recommended):
                return recommended
            tmp = curdir
            curdir = pardir
            pardir = os.path.abspath(os.path.join(tmp, os.pardir))
        return ""

    recommended_filename = find_recommended_file()
    prompt = "Please enter the filename of the content pack you have downloaded (%s): " % recommended_filename
    filename = raw_input(prompt)
    filename = os.path.expanduser(filename)
    if not filename:
        filename = recommended_filename
    while not validate_filename(filename):
        logger.error(
            "Error: couldn't open the specified file: \"%s\"\n" % filename)
        filename = raw_input(prompt)

    return filename


def detect_content_packs(options):

    if settings.RUNNING_IN_CI:  # skip if we're running on Travis
        logger.warning("Running in CI; skipping content pack download.")
        return

    preseeded_content_packs = False
    
    if os.path.exists(PRESEED_DIR) and not 'VIRTUAL_ENV' in os.environ.keys():
        for filename in os.listdir(PRESEED_DIR):
            fname_match = PRESEED_CONTENT_PACK_MASK.search(filename)
            if fname_match:
                lang = fname_match.group(1)
                call_command("retrievecontentpack", "local", lang, os.path.join(
                    PRESEED_DIR, filename), foreground=True)
                preseeded_content_packs = True

    if preseeded_content_packs:
        return

    # skip if we're not running in interactive mode (and it wasn't forced)
    if not options['interactive']:
        logger.warning(
            "Not running in interactive mode; skipping content pack download.")
        return

    logger.info(
        "\nIn order to access many of the available exercises, you need to "
        "load a content pack for the latest version."
        "\n"
        "If you have an Internet connection, you can download the needed "
        "file. Warning: this may take a long time!"
    )
    logger.info(
        "\n"
        "If you have already downloaded the content pack, you can specify the "
        "location of the file in the next step."
    )
    logger.info(
        "Otherwise, we will download it from {url}.".format(url=CONTENTPACK_URL)
    )

    if raw_input_yn("Do you wish to download and install the content pack now?"):
        ass_item_filename = CONTENTPACK_URL
        retrieval_method = "download"
    elif raw_input_yn("Do you have a local copy of the content pack already downloaded that you want to install?"):
        ass_item_filename = get_assessment_items_filename()
        retrieval_method = "local"
    else:
        ass_item_filename = None
        retrieval_method = "local"

    if not ass_item_filename:
        logger.warning(
            "No content pack given. You will need to download and install it later.")
    else:
        call_command("retrievecontentpack", retrieval_method,
                     "en", ass_item_filename, foreground=True)


class Command(BaseCommand):
    help = "Initialize or update the database."

    option_list = BaseCommand.option_list + (
        # Basic options
        # Functional options
        make_option('-u', '--username',
                    action='store',
                    dest='username',
                    default=None,
                    help='Superuser username'),
        make_option('-e', '--email',
                    action='store',
                    dest='email',
                    default="dummy@learningequality.org",
                    help='Superuser email address (optional)'),
        make_option('-p', '--password',
                    action='store',
                    dest='password',
                    default=None,
                    help='Superuser password'),
        make_option('-o', '--hostname',
                    action='store',
                    dest='hostname',
                    default=None,
                    help='Computer hostname'),
        make_option('-d', '--description',
                    action='store',
                    dest='description',
                    default="",
                    help='Computer description'),
        make_option('-n', '--noinput',
                    action='store_false',
                    dest='interactive',
                    default=True,
                    help='Run in non-interactive mode'),
        make_option('-a', '--dl-assessment-items',
                    action='store_true',
                    dest='force-assessment-item-dl',
                    default=False,
                    help='Downloads content pack from the url specified by CONTENTPACK_URL, without interaction'),
        make_option('-i', '--no-assessment-items',
                    action='store_true',
                    dest='no-assessment-items',
                    default=False,
                    help='Skip all steps associating with content pack downloading or the content database'),
    )

    def handle(self, *args, **options):
        if not options["interactive"]:
            options["hostname"] = options["hostname"] or get_host_name()

        # blank allows ansible scripts to dump errors cleanly.
        logger.info(
            "                                     \n"
            "   _   __  ___    _     _ _          \n"
            "  | | / / / _ \  | |   (_) |         \n"
            "  | |/ / / /_\ \ | |    _| |_ ___    \n"
            "  |    \ |  _  | | |   | | __/ _ \   \n"
            "  | |\  \| | | | | |___| | ||  __/   \n"
            "  \_| \_/\_| |_/ \_____/_|\__\___|   \n"
            "                                     \n"
            "https://learningequality.org/ka-lite/\n"
            "                                     \n"
            "         version {version:s}\n"
            "                                     ".format(
                version=VERSION
            )
        )

        if sys.version_info < (2, 7):
            raise CommandError(
                "Support for Python version 2.6 and below had been discontinued, please upgrade.")
        elif sys.version_info >= (2, 8):
            raise CommandError(
                "Your Python version is: %d.%d.%d -- which is not supported. Please use the Python 2.7 series or wait for Learning Equality to release Kolibri.\n" % sys.version_info[:3])
        elif sys.version_info < (2, 7, 6):
            logger.warning(
                "It's recommended that you install Python version 2.7.6. Your version is: %d.%d.%d\n" % sys.version_info[:3])

        if options["interactive"]:
            logger.info(
                "--------------------------------------------------------------------------------\n"
                "This script will configure the database and prepare it for use.\n"
                "--------------------------------------------------------------------------------\n"
            )
            raw_input("Press [enter] to continue...")

        # Assuming uid '0' is always root
        if not is_windows() and hasattr(os, "getuid") and os.getuid() == 0:
            logger.info(
                "-------------------------------------------------------------------\n"
                "WARNING: You are installing KA-Lite as root user!\n"
                "    Installing as root may cause some permission problems while running\n"
                "    as a normal user in the future.\n"
                "-------------------------------------------------------------------\n"
            )
            if options["interactive"]:
                if not raw_input_yn("Do you wish to continue and install it as root?"):
                    raise CommandError("Aborting script.\n")

        database_kind = settings.DATABASES["default"]["ENGINE"]
        if "sqlite" in database_kind:
            database_file = settings.DATABASES["default"]["NAME"]
        else:
            database_file = None

        database_exists = database_file and os.path.isfile(database_file)

        # An empty file is created automatically even when the database dosn't
        # exist. But if it's empty, it's safe to overwrite.
        database_exists = database_exists and os.path.getsize(
            database_file) > 0

        install_clean = not database_exists

        if database_file:
            if not database_exists:
                install_clean = True
            else:
                # We found an existing database file.  By default,
                #   we will upgrade it; users really need to work hard
                #   to delete the file (but it's possible, which is nice).
                logger.info(
                    "-------------------------------------------------------------------\n"
                    "WARNING: Database file already exists!\n"
                    "-------------------------------------------------------------------"
                )
                if not options["interactive"] \
                   or raw_input_yn("Keep database file and upgrade to KA Lite version %s? " % VERSION) \
                   or not raw_input_yn("Remove database file '%s' now? " % database_file) \
                   or not raw_input_yn("WARNING: all data will be lost!  Are you sure? "):
                    install_clean = False
                    logger.info("Upgrading database to KA Lite version %s" % VERSION)
                else:
                    install_clean = True
                    logger.info("OK.  We will run a clean install; ")
                    # After all, don't delete--just move.
                    logger.info(
                        "the database file will be moved to a deletable "
                        "location."
                    )

        if not install_clean and not database_file:
            # Make sure that, for non-sqlite installs, the database exists.
            raise Exception(
                "For databases not using SQLite, you must set up your database before running setup.")

        # Do all input at once, at the beginning
        if install_clean and options["interactive"]:
            if not options["username"] or not options["password"]:
                logger.info(
                    "Please choose a username and password for the admin account on this device.\n"
                    "    You must remember this login information, as you will need\n"
                    "    to enter it to administer this installation of KA Lite."
                )
            (username, password) = get_username_password(
                options["username"], options["password"])
            email = options["email"]
            (hostname, description) = get_hostname_and_description(
                options["hostname"], options["description"])
        else:
            username = options["username"] = (
                options["username"] or
                getattr(settings, "INSTALL_ADMIN_USERNAME", None) or
                get_clean_default_username()
            )
            password = options["password"] or getattr(
                settings, "INSTALL_ADMIN_PASSWORD", None)
            email = options["email"]  # default is non-empty
            hostname = options["hostname"]
            description = options["description"]

        if username and not validate_username(username):
            raise CommandError(
                "Username must contain only letters, digits, and underscores, and start with a letter.\n")

        ########################
        # Now do stuff
        ########################

        # Move database file (if exists)
        if install_clean and database_file and os.path.exists(database_file):
            if not settings.DB_TEMPLATE_DEFAULT or database_file != settings.DB_TEMPLATE_DEFAULT:
                # This is an overwrite install; destroy the old db
                dest_file = tempfile.mkstemp()[1]
                logger.info(
                    "(Re)moving database file to temp location, starting "
                    "clean install. Recovery location: {recovery:s}".format(
                        recovery=dest_file
                    )
                )
                shutil.move(database_file, dest_file)

        if settings.DB_TEMPLATE_DEFAULT and not database_exists and os.path.exists(settings.DB_TEMPLATE_DEFAULT):
            logger.info(
                "Copying database file from {0} to {1}".format(
                    settings.DB_TEMPLATE_DEFAULT,
                    settings.DEFAULT_DATABASE_PATH
                )
            )
            shutil.copy(
                settings.DB_TEMPLATE_DEFAULT, settings.DEFAULT_DATABASE_PATH)
        else:
            logger.info(
                "Baking a fresh database from scratch or upgrading existing "
                "database."
            )
            call_command(
                "syncdb", interactive=False, verbosity=options.get("verbosity"))
            call_command(
                "migrate", merge=True, verbosity=options.get("verbosity"))
        Settings.set("database_version", VERSION)

        # Copy all content item db templates
        reset_content_db(force=install_clean)

        # download the english content pack
        # This can take a long time and lead to Travis stalling. None of this
        # is required for tests, and does not apply to the central server.
        if options.get("no-assessment-items", False):

            logger.warning(
                "Skipping content pack downloading and configuration.")

        else:

            # user wants to force a new download; do it if we can, else error
            if options['force-assessment-item-dl']:
                call_command("retrievecontentpack", "download", "en")
            else:
                detect_content_packs(options)

        # Individually generate any prerequisite models/state that is missing
        if not Settings.get("private_key"):
            call_command("generatekeys", verbosity=options.get("verbosity"))
        if not Device.objects.count():
            call_command(
                "initdevice", hostname, description, verbosity=options.get("verbosity"))
        if not Facility.objects.count():
            Facility.initialize_default_facility()

        # Create the admin user
        # blank password (non-interactive) means don't create a superuser
        if password:
            admin = get_object_or_None(User, username=username)
            if not admin:
                call_command("createsuperuser", username=username, email=email,
                             interactive=False, verbosity=options.get("verbosity"))
                admin = User.objects.get(username=username)
            admin.set_password(password)
            admin.save()

        # Now deploy the static files
        logger.info("Copying static media...")
        ensure_dir(settings.STATIC_ROOT)

        call_command("collectstatic", interactive=False, verbosity=0, clear=True)
        call_command("collectstatic_js_reverse", interactive=False)

        # This is not possible in a distributed env
        if not settings.CENTRAL_SERVER:

            kalite_executable = 'kalite'
            if spawn.find_executable(kalite_executable):
                start_script_path = kalite_executable
            else:
                start_script_path = None

            # Run annotate_content_items, on the distributed server.
            logger.info(
                "Annotating availability of all content, checking for content "
                "in this directory: {content_root:s}".format(
                    content_root=settings.CONTENT_ROOT
                )
            )
            try:
                call_command("annotate_content_items")
            except OperationalError:
                pass

            # done; notify the user.
            logger.info(
                "\nCONGRATULATIONS! You've finished setting up the KA Lite "
                "server software."
            )
            logger.info(
                "You can now start KA Lite with the following command:"
                "\n\n"
                "    {kalite_cmd} start"
                "\n\n".format(
                    kalite_cmd=start_script_path
                )
            )

            if options['interactive'] and start_script_path:
                if raw_input_yn("Do you wish to start the server now?"):
                    logger.info("Running {0} start".format(start_script_path))
                    p = subprocess.Popen(
                        [start_script_path, "start"], env=os.environ)
                    p.wait()
