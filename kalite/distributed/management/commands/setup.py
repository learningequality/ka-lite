"""
Setup KA Lite:

 - Initialize database contents
 - Run migrations
 - Find and relocate obsolete user and data files
 - if interactive:
     - Download and unpack assessment items
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

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import kalite
from kalite.contentload.settings import KHAN_ASSESSMENT_ITEM_ROOT, OLD_ASSESSMENT_ITEMS_LOCATION
from kalite.topic_tools.settings import CHANNEL

from kalite.shared.warnings import RemovedInKALite_v016_Warning

from fle_utils.config.models import Settings
from fle_utils.general import get_host_name
from fle_utils.platforms import is_windows
from kalite.version import VERSION, SHORTVERSION
from kalite.facility.models import Facility
from securesync.models import Device
import warnings


# for extracting assessment item resources
ASSESSMENT_ITEMS_ZIP_URL = "https://learningequality.org/downloads/ka-lite/{version}/content/{channel}_assessment.zip".format(version=SHORTVERSION, channel=CHANNEL)


def raw_input_yn(prompt):
    ans = ""
    while True:
        ans = raw_input("%s (yes or no) " % prompt.strip()).lower()
        if ans in ["yes", "no"]:
            break
        logging.warning("Please answer yes or no.\n")
    return ans == "yes"


def raw_input_password():
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            logging.error("\tError: password must not be blank.\n")
            continue

        elif password != getpass.getpass("Password (again): "):
            logging.error("\tError: passwords did not match.\n")
            continue
        break
    return password


def clean_pyc(path):
    """Delete all *pyc files recursively in a path"""
    if not os.access(path, os.W_OK):
        warnings.warn(
            "{0} is not writable so cannot delete stale *pyc files".format(path))
        return
    print("Cleaning *pyc files (if writable) from: {0}".format(path))
    for root, __dirs, files in os.walk(path):
        pyc_files = filter(
            lambda filename: filename.endswith(".pyc"), files)
        py_files = set(
            filter(lambda filename: filename.endswith(".py"), files))
        excess_pyc_files = filter(
            lambda pyc_filename: pyc_filename[:-1] not in py_files, pyc_files)
        for excess_pyc_file in excess_pyc_files:
            full_path = os.path.join(root, excess_pyc_file)
            os.remove(full_path)


def validate_username(username):
    return bool(username and (not re.match(r'^[^a-zA-Z]', username) and not re.match(r'^.*[^a-zA-Z0-9_]+.*$', username)))


def get_clean_default_username():
    username = (getpass.getuser() or "").replace("-", "_")
    username = re.sub(r"\W", r"", username)  # Make sure auto-username doesn't have illegal characters
    return re.sub(r"^([^a-zA-Z])+", r"", username)  # Cut off non-alphabetic leading characters


def get_username(username):
    while not validate_username(username):

        username = raw_input("Username (leave blank to use '%s'): " %
                             get_clean_default_username()) or get_clean_default_username()
        if not validate_username(username):
            logging.error(
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
            logging.error("\tError: hostname must not be empty.\n")
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
        filename_guess = "{channel}_assessment.zip".format(channel=CHANNEL)
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
    prompt = "Please enter the filename of the assessment items package you have downloaded (%s): " % recommended_filename
    filename = raw_input(prompt)
    if not filename:
        filename = recommended_filename
    while not validate_filename(filename):
        logging.error(
            "Error: couldn't open the specified file: \"%s\"\n" % filename)
        filename = raw_input(prompt)

    return filename


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
                    help='Downloads assessment items from the url specified by ASSESSMENT_ITEMS_ZIP_URL, without interaction'),
        make_option('-i', '--no-assessment-items',
                    action='store_true',
                    dest='no-assessment-items',
                    default=False,
                    help='Skip all steps associating with assessment item downloading or the assessment item database'),
        make_option('-g', '--git-migrate',
                    action='store',
                    dest='git_migrate_path',
                    default=None,
                    help='Runs the gitmigrate management command to import data and content from previous installations of KA Lite'),
    )

    def handle(self, *args, **options):
        if not options["interactive"]:
            options["hostname"] = options["hostname"] or get_host_name()

        # blank allows ansible scripts to dump errors cleanly.
        print("                                     ")
        print("   _   __  ___    _     _ _          ")
        print("  | | / / / _ \  | |   (_) |         ")
        print("  | |/ / / /_\ \ | |    _| |_ ___    ")
        print("  |    \ |  _  | | |   | | __/ _ \   ")
        print("  | |\  \| | | | | |___| | ||  __/   ")
        print("  \_| \_/\_| |_/ \_____/_|\__\___|   ")
        print("                                     ")
        print("https://learningequality.org/ka-lite/")
        print("                                     ")
        print("         version %s" % VERSION)
        print("                                     ")

        if sys.version_info >= (2, 8) or sys.version_info < (2, 6):
            raise CommandError(
                "You must have Python version 2.6.x or 2.7.x installed. Your version is: %d.%d.%d\n" % sys.version_info[:3])
        if sys.version_info < (2, 7, 9):
            logging.warning(
                "It's recommended that you install Python version 2.7.9. Your version is: %d.%d.%d\n" % sys.version_info[:3])
            if sys.version_info < (2, 7):
                warnings.warn(
                    "Support for Python 2.6 will be discontinued in 0.16, please upgrade.",
                    RemovedInKALite_v016_Warning
                )


        if options["interactive"]:
            print(
                "--------------------------------------------------------------------------------")
            print(
                "This script will configure the database and prepare it for use.")
            print(
                "--------------------------------------------------------------------------------")
            raw_input("Press [enter] to continue...")

        # Tried not to be os-specific, but ... hey. :-/
        # benjaoming: This doesn't work, why is 502 hard coded!? Root is normally
        # '0' And let's not care about stuff like this, people can be free to
        # run this as root if they want :)
        if not is_windows() and hasattr(os, "getuid") and os.getuid() == 502:
            print(
                "-------------------------------------------------------------------")
            print("WARNING: You are installing KA-Lite as root user!")
            print(
                "\tInstalling as root may cause some permission problems while running")
            print("\tas a normal user in the future.")
            print(
                "-------------------------------------------------------------------")
            if options["interactive"]:
                if not raw_input_yn("Do you wish to continue and install it as root?"):
                    raise CommandError("Aborting script.\n")

        git_migrate_path = options["git_migrate_path"]

        if git_migrate_path:
            call_command("gitmigrate", path=git_migrate_path, interactive=options["interactive"])

        # TODO(benjaoming): This is used very loosely, what does it mean?
        # Does it mean that the installation path is clean or does it mean
        # that we should remove (clean) items from a previous installation?
        install_clean = not kalite.is_installed()

        database_kind = settings.DATABASES["default"]["ENGINE"]
        database_file = (
            "sqlite" in database_kind and settings.DATABASES["default"]["NAME"]) or None

        if database_file and os.path.exists(database_file):
            # We found an existing database file.  By default,
            #   we will upgrade it; users really need to work hard
            #   to delete the file (but it's possible, which is nice).
            print(
                "-------------------------------------------------------------------")
            print("WARNING: Database file already exists!")
            print(
                "-------------------------------------------------------------------")
            if not options["interactive"] \
               or raw_input_yn("Keep database file and upgrade to KA Lite version %s? " % VERSION) \
               or not raw_input_yn("Remove database file '%s' now? " % database_file) \
               or not raw_input_yn("WARNING: all data will be lost!  Are you sure? "):
                install_clean = False
                print("Upgrading database to KA Lite version %s" % VERSION)
            else:
                install_clean = True
                print("OK.  We will run a clean install; ")
                # After all, don't delete--just move.
                print(
                    "the database file will be moved to a deletable location.")

        if not install_clean and not database_file and not kalite.is_installed():
            # Make sure that, for non-sqlite installs, the database exists.
            raise Exception(
                "For databases not using SQLite, you must set up your database before running setup.")

        # Do all input at once, at the beginning
        if install_clean and options["interactive"]:
            if not options["username"] or not options["password"]:
                print(
                    "Please choose a username and password for the admin account on this device.")
                print(
                    "\tYou must remember this login information, as you will need")
                print(
                    "\tto enter it to administer this installation of KA Lite.")
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
            password = options["password"] or getattr(settings, "INSTALL_ADMIN_PASSWORD", None)
            email = options["email"]  # default is non-empty
            hostname = options["hostname"]
            description = options["description"]

        if username and not validate_username(username):
            raise CommandError(
                "Username must contain only letters, digits, and underscores, and start with a letter.\n")

        ########################
        # Now do stuff
        ########################

        # Clean *pyc files if we are in a git repo
        if settings.IS_SOURCE:
            clean_pyc(settings.SOURCE_DIR)
        else:
            # Because we install dependencies as data_files, we run into problems,
            # namely that the pyc files are left dangling.
            distributed_packages = [
                os.path.join(kalite.ROOT_DATA_PATH, 'dist-packages'),
                os.path.join(kalite.ROOT_DATA_PATH, 'python-packages'),
            ]
            # Try locating django
            for dir_to_clean in distributed_packages:
                clean_pyc(dir_to_clean)

        # Move database file (if exists)
        if install_clean and database_file and os.path.exists(database_file):
            # This is an overwrite install; destroy the old db
            dest_file = tempfile.mkstemp()[1]
            print(
                "(Re)moving database file to temp location, starting clean install. Recovery location: %s" % dest_file)
            shutil.move(database_file, dest_file)

        # benjaoming: Commented out, this hits the wrong directories currently
        # and should not be necessary.
        # If we have problems with pyc files, we're doing something else wrong.
        # See https://github.com/learningequality/ka-lite/issues/3487

        # Should clean_pyc for (clean) reinstall purposes
        # call_command("clean_pyc", interactive=False, verbosity=options.get("verbosity"), path=os.path.join(settings.PROJECT_PATH, ".."))

        # Migrate the database
        call_command("syncdb", interactive=False, verbosity=options.get("verbosity"))
        call_command("migrate", merge=True, verbosity=options.get("verbosity"))
        Settings.set("database_version", VERSION)

        # download assessment items
        # This can take a long time and lead to Travis stalling. None of this
        # is required for tests, and does not apply to the central server.
        if options.get("no-assessment-items", False):

            logging.warning("Skipping assessment item downloading and configuration.")

        else:

            call_command("syncdb", interactive=False, verbosity=options.get("verbosity"), database="assessment_items")

            # Outdated location of assessment items - move assessment items from their
            # old location (CONTENT_ROOT/khan where they were mixed with other content
            # items)

            # TODO(benjaoming) for 0.15, remove the "move assessment items"
            # mechanism
            writable_assessment_items = os.access(KHAN_ASSESSMENT_ITEM_ROOT, os.W_OK)

            # Remove old assessment items
            if os.path.exists(OLD_ASSESSMENT_ITEMS_LOCATION) and os.access(OLD_ASSESSMENT_ITEMS_LOCATION, os.W_OK):
                logging.info("Deleting old assessment items")
                shutil.rmtree(OLD_ASSESSMENT_ITEMS_LOCATION)

            if writable_assessment_items and options['force-assessment-item-dl']:
                call_command(
                    "unpack_assessment_zip", ASSESSMENT_ITEMS_ZIP_URL)
            elif options['force-assessment-item-dl']:
                raise RuntimeError(
                    "Got force-assessment-item-dl but directory not writable")
            elif not settings.ASSESSMENT_ITEMS_SYSTEM_WIDE and not settings.RUNNING_IN_TRAVIS and options['interactive']:
                print(
                    "\nStarting in version 0.13, you will need an assessment items package in order to access many of the available exercises.")
                print(
                    "If you have an internet connection, you can download the needed package. Warning: this may take a long time!")
                print(
                    "If you have already downloaded the assessment items package, you can specify the file in the next step.")
                print("Otherwise, we will download it from {url}.".format(
                    url=ASSESSMENT_ITEMS_ZIP_URL))

                if raw_input_yn("Do you wish to download the assessment items package now?"):
                    ass_item_filename = ASSESSMENT_ITEMS_ZIP_URL
                elif raw_input_yn("Have you already downloaded the assessment items package?"):
                    ass_item_filename = get_assessment_items_filename()
                else:
                    ass_item_filename = None

                if not ass_item_filename:
                    logging.warning(
                        "No assessment items package file given. You will need to download and unpack it later.")
                else:
                    call_command("unpack_assessment_zip", ass_item_filename)

            elif options['interactive'] and not settings.ASSESSMENT_ITEMS_SYSTEM_WIDE:
                logging.warning(
                    "Assessment item directory not writable, skipping download.")
            elif not settings.ASSESSMENT_ITEMS_SYSTEM_WIDE:
                logging.warning(
                    "No assessment items package file given. You will need to download and unpack it later.")
            else:
                print("Found bundled assessment items")

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
        logging.info("Copying static media...")
        call_command("collectstatic", interactive=False, verbosity=0)
        call_command("collectstatic_js_reverse", interactive=False)

        # This is not possible in a distributed env
        if not settings.CENTRAL_SERVER:

            kalite_executable = 'kalite'
            if not spawn.find_executable('kalite'):
                if os.name == 'posix':
                    start_script_path = os.path.realpath(
                        os.path.join(settings.PROJECT_PATH, "..", "bin", kalite_executable))
                else:
                    start_script_path = os.path.realpath(
                        os.path.join(settings.PROJECT_PATH, "..", "bin", "windows", "kalite.bat"))
            else:
                start_script_path = kalite_executable

            # Run videoscan, on the distributed server.
            print("Scanning for video files in the content directory (%s)" %
                  settings.CONTENT_ROOT)
            call_command("videoscan")

            # done; notify the user.
            print("\nCONGRATULATIONS! You've finished setting up the KA Lite server software.")
            print("You can now start KA Lite with the following command:\n\n\t%s start\n\n" % start_script_path)

            if options['interactive']:
                if raw_input_yn("Do you wish to start the server now?"):
                    print("Running {0} start".format(start_script_path))
                    p = subprocess.Popen([start_script_path, "start"], env=os.environ)
                    p.wait()
