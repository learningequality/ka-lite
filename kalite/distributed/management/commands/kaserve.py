"""
This is a command-line tool to execute functions helpful to testing.
"""
import os
import sys
import time
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from fle_utils.chronograph.models import Job
from fle_utils.config.models import Settings
from fle_utils.general import isnumeric
from fle_utils.internet import get_ip_addresses
from kalite.topic_tools import get_topic_tree
from kalite.updates import stamp_availability_on_topic
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
            help="Daemonize the server. Relevant only when we're running the CherryPy server (a.k.a. when running with the --production option)"
        ),
        make_option(
            '--pidfile',
            action='store',
            dest='pidfile',
            default=os.path.join(settings.PROJECT_PATH, "runcherrypyserver.pid"),
            help="PID file"
        ),
        make_option(
            '--production',
            action='store_true',
            dest='production',
            default=not settings.DEBUG,
            help="Whether to run the production wsgi server (CherryPy). If False, run the development server"
        ),
    )

    def setup_server_if_needed(self):
        """Run the setup command, if necessary."""

        try: # Ensure that the database has been synced and a Device has been created
            assert Settings.get("private_key") and Device.objects.count()
        except (DatabaseError, AssertionError): # Otherwise, run the setup command
            self.stdout.write("Setting up KA Lite; this may take a few minutes; please wait!\n")
            call_command("setup", interactive=False)
        # Double check that the setup process successfully created a Device
        assert Settings.get("private_key") and Device.objects.count(), "There was an error configuring the server. Please report the output of this command to Learning Equality."

    def reinitialize_server(self):
        """Reset the server state."""
        logging.info("Invalidating the web cache.")
        from fle_utils.internet.webcache import invalidate_web_cache
        invalidate_web_cache()

        # Next, call videoscan.
        logging.info("Running videoscan.")
        call_command("videoscan")

        # Finally, pre-load global data
        def preload_global_data():
            logging.info("Preloading topic data.")
            stamp_availability_on_topic(get_topic_tree(), force=True, stamp_urls=True)
        preload_global_data()


    def handle(self, *args, **options):
        # Eliminate irrelevant settings
        for opt in BaseCommand.option_list:
            del options[opt.dest]

        # In case any chronograph threads were interrupted the last time
        # the server was stopped, clear their is_running flags to allow
        # them to be started up again as needed.
        Job.objects.update(is_running=False)

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

        call_command("collectstatic", interactive=False)

        # set the BUILD_HASH to the current time, so assets get refreshed to their newest versions
        build_hash = str(time.mktime(time.gmtime()))
        logging.debug("Writing %s as BUILD_HASH" % build_hash)
        Settings.set('BUILD_HASH', build_hash)

        # Now call the proper command
        if not options["production"]:
            call_command("runserver", "%s:%s" % (options["host"], options["port"]))
        else:
            del options["production"]
            sys.stdout.write("To access KA Lite from another connected computer, try the following address(es):\n")
            for addr in get_ip_addresses():
                sys.stdout.write("\thttp://%s:%s/\n" % (addr, settings.USER_FACING_PORT()))
            call_command("runcherrypyserver", *["%s=%s" % (key,val) for key, val in options.iteritems()])
