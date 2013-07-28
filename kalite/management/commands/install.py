import getpass
import os
import platform
import pwd
import re
import shutil
import sys
import tempfile
from optparse import make_option

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

from kalite.utils.general import get_host_name


def raw_input_yn(prompt):
    ans = ""
    while True:
        ans = raw_input("%s (yes or no) " % prompt.strip()).lower()
        if ans in ["yes", "no"]:
            break
        print "Please answer yes or no."
    return ans == "yes"


def raw_input_password():
    while True:
        password = getpass.getpass("Password: ")
        if not password:
            print "\tError: password must not be blank."
            continue

        elif password != getpass.getpass("Password (again): "):
            print "\tError: passwords did not match."
            continue
        break
    return password


def find_owner(file):
    return pwd.getpwuid(os.stat(file).st_uid).pw_name


def get_username(current_user):
    while True:
        
        username = raw_input("Username (leave blank to use '%s'): " % current_user) or current_user
        if re.match(r'^[^a-zA-Z]', username) or re.match(r'[^a-zA-Z0-9_]+', username):
            print "\tError: Username must contain only letters, digits, and underscores, and start with a letter."
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
            print "\tError: hostname must not be empty."
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
            dest='hostame',
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
        print "  _   __  ___    _     _ _        "
        print " | | / / / _ \  | |   (_) |       "
        print " | |/ / / /_\ \ | |    _| |_ ___  "
        print " |    \ |  _  | | |   | | __/ _ \ "
        print " | |\  \| | | | | |___| | ||  __/ "
        print " \_| \_/\_| |_/ \_____/_|\__\___| "
        print "                                  "
        print "http://kalite.learningequality.org"
        print "                                  "

        if options["interactive"]:
            print "--------------------------------------------------------------------------------"
            print
            print "This script will configure the database and prepare it for use."
            print
            print "--------------------------------------------------------------------------------"
            print
            raw_input("Press [enter] to continue...")
            print

        if platform.platform() != "Windows" and os.getuid() == 502:
            print "-------------------------------------------------------------------"
            print "You are installing KA-Lite as root user!"
            print "Installing as root may cause some permission problems while running"
            print "as a normal user in the future."
            print "-------------------------------------------------------------------"
            print
            if not options["interactive"] or not raw_input_yn("Do you wish to continue and install it as root?"):
                sys.exit(1)
            print 

        # Check to see if the current user is the owner of the install directory
        current_owner = find_owner(BASE_DIR)
        current_user = getpass.getuser()
        if current_owner != current_user:
            print "-------------------------------------------------------------------"
            print "You are not the owner of this directory!"
            print "Please copy all files to a directory that you own and then" 
            print "re-run this script."
            print "-------------------------------------------------------------------"
            sys.exit(1)

        if not os.access(BASE_DIR, os.W_OK):
            print "-------------------------------------------------------------------"
            print "You do not have permission to write to this directory!"
            print "-------------------------------------------------------------------"
            sys.exit(1)

        database_file = os.path.join(BASE_DIR, "kalite/database/data.sqlite")
        if os.path.exists(database_file):
            print "-------------------------------------------------------------------"
            print "Error: Database file already exists! If this is a new installation,"
            print "you should delete the file kalite/database/data.sqlite and then"
            print "re-run this script. If the server is running, first run ./stop.sh"
            print "-------------------------------------------------------------------"
            if not options["interactive"] or not raw_input_yn("Remove database file '%s' now? " % database_file):
                print "Aborting installation."
                sys.exit(1)
            elif not raw_input_yn("WARNING: all data will be lost!  Are you sure? "):
                print "Aborting installation."
                sys.exit(1)
            else:
                shutil.move(database_file, tempfile.mkstemp()[1])
            print

        if sys.version_info >= (2,8) or sys.version_info < (2,6):
                print "----------------------------------------------------------------"
                print "Error: You must have Python version 2.6.x or 2.7.x installed. Your version is: %s" % sys.version_info
                print "----------------------------------------------------------------"
                sys.exit(1)

        # Do all input at once, at the beginning
        print
        print "Please choose a username and password for the admin account on this device."
        print "You must remember this login information, as you will need to enter it to"
        print "administer this installation of KA Lite."
        print
        if options["interactive"]:
            (username, password) = get_username_password(current_user)
            (hostname, description) = get_hostname_and_description()
        else:
            username = options["username"]
            password = options["password"]
            hostname = options["hostname"]
            description = options["description"]

        # Now do stuff
        call_command("syncdb", migrate=True, interactive=False)

        # TODO(bcipolli): this should be done in initapache
        # set the database permissions so that Apache will be able to access them
        # chmod 777 database
        # chmod 766 database/data.sqlite

        call_command("generatekeys")

        call_command("createsuperuser", username=username, email="dummy@learningequality.org", interactive=False)
        User.objects.get(username=username).set_password(password)

        call_command("initdevice", hostname, description)

        print
        print "CONGRATULATIONS! You've finished installing the KA Lite server software."
        print "Please run './start.sh' to start the server, and then load the url"
        print "http://127.0.0.1:8008/ to complete the device configuration."
        print
