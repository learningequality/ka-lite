import glob
import logging
import os
import shutil
import time

from distutils.dir_util import copy_tree

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option


def get_old_installation_path():

    while True:

        path = raw_input("Please enter the path of the previous installation of KA Lite (version 0.13 or below): ")

        if os.path.exists(os.path.join(path, "kalite", "database")):
            break
        else:
            logging.error("The specified path did not contain a valid KA Lite installation (version 0.13 or below). Please try again.")

    return path


def get_old_content_path(default):

    while True:

        path = raw_input("Please enter path you would like to import videos from (press Enter to choose '%s')? " % default) or default

        if os.path.exists(path):
            break
        else:
            logging.error("The specified path did not exist. Please try again.")

    return path


def raw_input_options(prompt, options, reminder="Please provide a valid response."):

    while True:

        ans = raw_input(prompt + " ").strip().lower()
        if ans in options:
            return ans
        print reminder


def get_glob_size_in_mb(pathglob):
     return sum([os.path.getsize(f) for f in glob.glob(pathglob)]) / 1048576


class Command(BaseCommand):
    """
    This command takes an argument for the path to a git based installation of KA Lite (version 0.13 or below).
    It then copies the database file from the old location to the location needed for the current installation of KA Lite.
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--path',
            action='store',
            dest='path',
            default=None,
            help="Path of previous KA Lite installation (version 0.13 or below) from which to import",
        ),
        make_option('-n', '--noinput',
            action='store_false',
            dest='interactive',
            default=True,
            help='Run in non-interactive mode',
        ),
    )

    def handle(self, *args, **options):

        interactive = options.get("interactive")

        try:
            path = options.get("path") or args[0]
        except IndexError:
            path = None

        if not path:

            if interactive:
                path = get_old_installation_path()
            else:
                raise CommandError("Must specify a path for the old installation of KA Lite to import data from, using --path argument.")

        print
        print "-------------------------------------------------------------------"
        print "Attempting to copy database file from previous installation"
        print "-------------------------------------------------------------------\n"

        old_database_path = os.path.join(path, "kalite", "database", "data.sqlite")

        if not os.path.exists(os.path.split(old_database_path)[0]):
            raise CommandError("No database folder found to import from")

        if not os.path.exists(old_database_path):

            print "No database file found. Continuing."

        else:

            # Backup any existing database before overwriting it
            if os.path.exists(settings.DEFAULT_DATABASE_PATH):
                backup_db_path = settings.DEFAULT_DATABASE_PATH + ".%d.bak" % int(time.time())
                print "Backing up existing database file in new KA Lite installation ('%s') to '%s'..." % (settings.DEFAULT_DATABASE_PATH, backup_db_path),
                shutil.copy(settings.DEFAULT_DATABASE_PATH, backup_db_path)
                print "done."

            # Copy in the old database to the new location
            print "Copying old database ('%s') into correct location for new version of KA Lite ('%s')..." % (old_database_path, settings.DEFAULT_DATABASE_PATH),
            shutil.copy(old_database_path, settings.DEFAULT_DATABASE_PATH)
            print "done."

            # Copy in the old database to the new location
            print "Renaming old database ('%s') to '%s' to prevent it from being used in the old version of KA Lite anymore..." % (old_database_path, os.path.split(old_database_path)[-1] + ".donotuse"),
            shutil.move(old_database_path, old_database_path + ".donotuse")
            print "done."

        print
        print "-------------------------------------------------------------------"
        print "Attempting to move or copy content files from previous installation"
        print "-------------------------------------------------------------------\n"

        # Determine where to import content from, confirming with the user (if we're in interactive mode)
        old_content_path = os.path.join(path, "content")
        if interactive:
            old_content_path = get_old_content_path(default=old_content_path)

        # Get some file size stats about the old content path
        video_size_mb = get_glob_size_in_mb(os.path.join(old_content_path, "*.mp4"))
        image_size_mb = get_glob_size_in_mb(os.path.join(old_content_path, "*.png"))

        # Determine whether to copy, or move, the content (default to "move")
        if not interactive:
            move_content = True
        else:
            move_content = raw_input_options(
                "Would you like to move, or copy, the %dmb of videos and %dmb of thumbnails from '%s' to '%s'?" % (video_size_mb, image_size_mb, old_content_path, settings.CONTENT_ROOT),
                ["move","copy","c","m"],
                "Please enter either 'move' or 'copy'."
            ).startswith("m")
        clone_fn = shutil.move if move_content else shutil.copy
        clone_name = "Moving" if move_content else "Copying"

        if not os.path.exists(old_content_path):
            raise CommandError("No content folder found to be imported")

        for filepath in glob.glob(os.path.join(old_content_path, "*.mp4")) + glob.glob(os.path.join(old_content_path, "*.png")):
            filename = os.path.split(filepath)[-1]
            destination_path = os.path.join(settings.CONTENT_ROOT, filename)
            print "%s %s to %s..." % (clone_name, filepath, destination_path),
            clone_fn(filepath, destination_path)
            print "done."

        print "Finished %s content into new directory. Enjoy!" % clone_name.lower()