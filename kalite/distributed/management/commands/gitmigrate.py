import os
import shutil

from distutils.dir_util import copy_tree

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings; logging = settings.LOG

from optparse import make_option


class Command(BaseCommand):
    """
    This command takes an argument for the path to a git based installation of KA Lite.
    It then copies the database file from there to the current location of KA Lite (if the two are different).
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--path',
            action='store',
            dest='path',
            default=None,
            help="Git Install Path"
        ),
    )

    def handle(self, *args, **options):
        try:
            path = options.get("path") or args[0]
        except IndexError:
            path = None

        if not path:
            # This is necessary, as simply specifying "" means you are trying to migrate something onto itself
            raise CommandError("Must specify a path to migrate the Git installed version of KA Lite from")

        if not os.path.exists(os.path.join(path, "kalite", "database", "data.sqlite")):
            raise CommandError("No database file found to migrate")
        else:
            shutil.copy2(os.path.join(path, "kalite", "database", "data.sqlite"), os.path.join(os.environ.get("KALITE_DIR"), "kalite", "database", "data.sqlite"))
            logging.info("Database file successfully copied")

        if not os.path.exists(os.path.join(path, "content")):
            raise CommandError("No content folder find to migrate")
        else:
            output = copy_tree(os.path.join(path, "content"), os.path.join(os.environ.get("KALITE_DIR"), "content"), update=True)
            logging.info("Copied {files} files from the previous content folder".format(files=len(output)))
