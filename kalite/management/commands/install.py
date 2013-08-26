import getpass
import os
import re
import shutil
import sys
import tempfile
from optparse import make_option

# This is necessary for this script to run before KA Lite has ever been installed.
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.realpath(CURRENT_DIR + "/../../../")

sys.path = [
    os.path.join(BASE_DIR, "python-packages"),
    os.path.join(BASE_DIR, "kalite")
] + sys.path
os.environ["DJANGO_SETTINGS_MODULE"] = "kalite.settings"  # allows django commands to run

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings
import version
from kalite.utils.general import get_host_name
from kalite.utils.platforms import is_windows, system_script_extension


def raw_input_yn(prompt):
    ans = ""
    while True:
        ans = raw_input("%s (yes or no) " % prompt.strip()).lower()
        if ans in ["yes", "no"]:
            break
        sys.stderr.write("Please answer yes or no.\n")
    return ans == "yes"


def raw_input_password():
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            sys.stderr.write("\tError: password must not be blank.\n")
            continue

        elif password != getpass.getpass("Password (again): "):
            sys.stderr.write("\tError: passwords did not match.\n")
            continue
        break
    return password


def find_owner(file):
    return getpass.getuser()

def validate_username(username):
    return not username or (not re.match(r'^[^a-zA-Z]', username) and not re.match(r'[^a-zA-Z0-9_]+', username))

def get_username(current_user):
    while True:
        
        username = raw_input("Username (leave blank to use '%s'): " % current_user) or current_user
        if not validate_username(username):
            sys.stderr.write("\tError: Username must contain only letters, digits, and underscores, and start with a letter.\n")
        else:
            break
    return username


def get_username_password(current_user=""):
    return (get_username(current_user), raw_input_password())


def get_hostname_and_description():
    default_hostname = get_host_name()
    while True:
        prompt = "Please enter a name for this server%s: " % ("" if not default_hostname else (" (or, press Enter to use '%s')" % get_host_name()))
        hostname = raw_input(prompt) or default_hostname
        if not hostname:
            sys.stderr.write("\tError: hostname must not be empty.\n")
        else:
            break

    description = raw_input("Please enter a one-line description for this server (or, press Enter to leave blank): ")

    return (hostname, description)



class Command(BaseCommand):
    help = "Create a zip file with all code, that can be unpacked anywhere."

    option_list = BaseCommand.option_list + (
        # Basic options
        # Functional options
        make_option('-u', '--username',
            action='store',
            dest='username',
            default=getpass.getuser(),
            help='Superuser username'),
        make_option('-p', '--password',
            action='store',
            dest='password',
            default=None,
            help='Superuser password'),
        make_option('-o', '--hostname',
            action='store',
            dest='hostname',
            default=get_host_name(),
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
            help='FILE to save zip to',
            metavar="FILE"),
        )

    def handle(self, *args, **options):
        sys.stdout.write("  _   __  ___    _     _ _        \n")
        sys.stdout.write(" | | / / / _ \  | |   (_) |       \n")
        sys.stdout.write(" | |/ / / /_\ \ | |    _| |_ ___  \n")
        sys.stdout.write(" |    \ |  _  | | |   | | __/ _ \ \n")
        sys.stdout.write(" | |\  \| | | | | |___| | ||  __/ \n")
        sys.stdout.write(" \_| \_/\_| |_/ \_____/_|\__\___| \n")
        sys.stdout.write("                                  \n")
        sys.stdout.write("http://kalite.learningequality.org\n")
        sys.stdout.write("                                  \n")
        sys.stdout.write("         version %s\n" % version.VERSION)
        sys.stdout.write("                                  \n")

        if sys.version_info >= (2,8) or sys.version_info < (2,6):
            raise CommandError("You must have Python version 2.6.x or 2.7.x installed. Your version is: %s\n" % sys.version_info)

        if options["interactive"]:
            sys.stdout.write("--------------------------------------------------------------------------------\n")
            sys.stdout.write("\n")
            sys.stdout.write("This script will configure the database and prepare it for use.\n")
            sys.stdout.write("\n")
            sys.stdout.write("--------------------------------------------------------------------------------\n")
            sys.stdout.write("\n")
            raw_input("Press [enter] to continue...")
            sys.stdout.write("\n")

        # Tried not to be os-specific, but ... hey. :-/
        if not is_windows() and hasattr(os, "getuid") and os.getuid() == 502:
            sys.stdout.write("-------------------------------------------------------------------\n")
            sys.stdout.write("WARNING: You are installing KA-Lite as root user!\n")
            sys.stdout.write("\tInstalling as root may cause some permission problems while running\n")
            sys.stdout.write("\tas a normal user in the future.\n")
            sys.stdout.write("-------------------------------------------------------------------\n")
            if options["interactive"]:
                if not raw_input_yn("Do you wish to continue and install it as root?"):
                    raise CommandError("Aborting script.\n")
                sys.stdout.write("\n")

        # Check to see if the current user is the owner of the install directory
        current_owner = find_owner(BASE_DIR)
        current_user = getpass.getuser()
        if current_owner != current_user:
            raise CommandError("""You are not the owner of this directory!
    Please copy all files to a directory that you own and then
    re-run this script.""")

        if not os.access(BASE_DIR, os.W_OK):
            raise CommandError("You do not have permission to write to this directory!")

        install_clean = False
        database_file = settings.DATABASES["default"]["NAME"]
        if os.path.exists(database_file):
            # We found an existing database file.  By default,
            #   we will upgrade it; users really need to work hard
            #   to delete the file (but it's possible, which is nice).
            sys.stdout.write("-------------------------------------------------------------------\n")
            sys.stdout.write("WARNING: Database file already exists! \n")
            sys.stdout.write("-------------------------------------------------------------------\n")
            if not options["interactive"] \
               or raw_input_yn("Keep database file and upgrade to KA Lite version %s? " % version.VERSION) \
               or not raw_input_yn("Remove database file '%s' now? " % database_file) \
               or not raw_input_yn("WARNING: all data will be lost!  Are you sure? "):
                install_clean = False
                sys.stdout.write("Upgrading database to KA Lite version %s\n" % version.VERSION)
            else:
                # After all, don't delete--just move.
                install_clean = True
                sys.stdout.write("OK.  We will run a clean install; database file will be moved to a deletable location.")

        # Do all input at once, at the beginning
        if install_clean:
            if options["interactive"]:
                sys.stdout.write("\n")
                sys.stdout.write("Please choose a username and password for the admin account on this device.\n")
                sys.stdout.write("\tYou must remember this login information, as you will need to enter it to\n")
                sys.stdout.write("\tadminister this installation of KA Lite.\n")
                sys.stdout.write("\n")
                (username, password) = get_username_password(current_user)
                (hostname, description) = get_hostname_and_description()
            else:
                username = options["username"]
                password = options["password"]
                hostname = options["hostname"]
                description = options["description"]

                if not validate_username(username):
                    raise CommandError("Username must contain only letters, digits, and underscores, and start with a letter.\n")
                elif not password:
                    raise CommandError("Password cannot be blank.\n")

        # Now do stuff
        if install_clean:
            dest_file = tempfile.mkstemp()[1]
            sys.stdout.write("(Re)moving database file to temp location, starting clean install.  Recovery location: %s\n" % dest_file)
            shutil.move(database_file, dest_file)

        # Got this far, it's OK to stop the server.
        import serverstop

        # Should clean_pyc for (clean) reinstall purposes
        call_command("clean_pyc", migrate=True, interactive=False, verbosity=options.get("verbosity"))

        # 
        call_command("syncdb", migrate=True, interactive=False, verbosity=options.get("verbosity"))

        if install_clean:
            call_command("generatekeys", verbosity=options.get("verbosity"))

            call_command("createsuperuser", username=username, email="dummy@learningequality.org", interactive=False, verbosity=options.get("verbosity"))
            admin = User.objects.get(username=username)
            admin.set_password(password)
            admin.save()

            call_command("initdevice", hostname, description, verbosity=options.get("verbosity"))

        sys.stdout.write("\n")
        sys.stdout.write("CONGRATULATIONS! You've finished installing the KA Lite server software.\n")
        sys.stdout.write("\tPlease run './start.%s' to start the server, and then load the url\n" % system_script_extension())
        sys.stdout.write("\thttp://127.0.0.1:%d/ to complete the device configuration.\n" % settings.PRODUCTION_PORT)
        sys.stdout.write("\n")
