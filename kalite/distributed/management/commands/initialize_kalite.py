"""
This is a command-line tool to execute functions helpful to testing.
"""

from django.conf import settings
logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from fle_utils.config.models import Settings
from kalite.caching import initialize_content_caches
from securesync.models import Device


class Command(BaseCommand):
    help = (
        "Initializes the server before cherrypy or whatever starts. This is to "
        "ensure that all is ready..."
    )
    option_list = BaseCommand.option_list + (
    )

    def setup_server_if_needed(self):
        """Run the setup command, if necessary.
            It's necessary if the Settings model doesn't have a "database_version" or if that version doesn't match
            kalite.version.VERSION, indicating the source has been changed. Then setup is run to create/migrate the db.
        """

        try:
            from kalite.version import VERSION
            assert Settings.get("database_version") == VERSION
        except (DatabaseError, AssertionError):
            logging.info("Setting up KA Lite; this may take a few minutes; please wait!\n")
            call_command("setup", interactive=False)
            # Double check the setup process worked ok.
            assert Settings.get("database_version") == VERSION, "There was an error configuring the server. Please report the output of this command to Learning Equality."

    def reinitialize_server(self):
        """Reset the server state."""

        # Next, call videoscan.
        logging.info("Running videoscan.")
        call_command("videoscan")

        # Finally, pre-load global data
        initialize_content_caches()

    def handle(self, *args, **options):

        self.setup_server_if_needed()

        # we do this on every server request,
        # as we don't know what happens when we're not looking.
        self.reinitialize_server()

        # Copy static media, one reason for not symlinking: It is not cross-platform and can cause permission issues
        # with many webservers
        logging.info("Copying static media...")
        call_command("collectstatic", interactive=False, verbosity=0)
        call_command("collectstatic_js_reverse", interactive=False)
