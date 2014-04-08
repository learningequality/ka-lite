"""
This is a command-line tool to execute functions helpful to testing.
"""
import os
import sys
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils.translation import ugettext as _

from fle_utils.config.models import Settings
from fle_utils.django_utils import call_command_with_output
from fle_utils.general import isnumeric
from fle_utils.internet import get_ip_addresses
from kalite.facility.models import Facility
from securesync.models import Device


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--host',
            action='store',
            dest='host',
            default="0.0.0.0",
            help="Host"
        ),
        make_option(
            '--port',
            action='store',
            dest='port',
            default=settings.PRODUCTION_PORT,
            help="Port"
        ),
        make_option(
            '--threads',
            action='store',
            dest='threads',
            default=settings.CHERRYPY_THREAD_COUNT,
            help="Thread count"
        ),
        make_option(
            '--daemonize',
            action='store_true',
            dest='daemonize',
            default=False,
            help="Daemonize"
        ),
        make_option(
            '--pidfile',
            action='store',
            dest='pidfile',
            default=os.path.join(settings.PROJECT_PATH, "runcherrypyserver.pid"),
            help="PID file"
        ),
    )

    def setup_server_if_needed(self):
        """Run the setup command, if necessary."""

        # Now, validate the server.
        try:
            if Settings.get("private_key") and Device.objects.count():
                # The only success case
                pass

            elif not Device.objects.count():
                # Nothing we can do to recover
                raise CommandError("You are screwed, buddy--you went through setup but you have no devices defined!  Call for help!")

            else:
                # Force hitting recovery code, by raising a generic error
                #   that gets us to the "except" clause
                raise DatabaseError

        except DatabaseError:
            self.stdout.write("Setting up KA Lite; this may take a few minutes; please wait!\n")

            call_command("setup", interactive=False)  # show output to the user
            #out = call_command_with_output("setup", interactive=False)
            #if out[1] or out[2]:
            #    # Failed; report and exit
            #    self.stderr.write(out[1])
            #    raise CommandError("Failed to setup/recover.")

    def reinitialize_server(self):
        """Reset the server state."""
        if not settings.CENTRAL_SERVER:
            logging.info("Invalidating the web cache.")
            from fle_utils.internet.webcache import invalidate_web_cache
            invalidate_web_cache()

            # Next, call videoscan.
            logging.info("Running videoscan.")
            call_command("videoscan")

        # Finally, pre-load global data
        def preload_global_data():
            if not settings.CENTRAL_SERVER:
                logging.info("Preloading topic data.")
                from kalite.main.topic_tools import get_topic_tree
                from kalite.updates import stamp_availability_on_topic
                stamp_availability_on_topic(get_topic_tree(), force=True, stamp_urls=True)
        preload_global_data()


    def handle(self, *args, **options):
        # Eliminate irrelevant settings
        for opt in BaseCommand.option_list:
            del options[opt.dest]

        # Parse the crappy way that runcherrypy takes args,
        #   or the host/port
        for arg in args:
            if "=" in arg:
                (key,val) = arg.split("=")
                options[key] = val
            elif ":" in arg:
                (options["host"], options["port"]) = arg.split(":")
            elif isnumeric(arg):
                options["port"] = arg
            else:
                raise CommandError("Unexpected argument format: %s" % arg)

        # In order to avoid doing this twice when the autoreloader
        #   loads this process again, only execute the initialization
        #   code if autoreloader won't be run (daemonize), or if
        #   RUN_MAIN is set (autoreloader has started)
        if options["daemonize"] or os.environ.get("RUN_MAIN"):
            self.setup_server_if_needed()

            # we do this on every server request,
            # as we don't know what happens when we're not looking.
            self.reinitialize_server()

        # Now call the proper command
        if not options["daemonize"]:
            call_command("runserver", "%s:%s" % (options["host"], options["port"]))
        else:
            call_command("collectstatic", interactive=False)
            sys.stdout.write("To access KA Lite from another connected computer, try the following address(es):\n")
            for addr in get_ip_addresses():
                sys.stdout.write("\thttp://%s:%s/\n" % (addr, settings.USER_FACING_PORT()))
            call_command("runcherrypyserver", *["%s=%s" % (key,val) for key, val in options.iteritems()])
