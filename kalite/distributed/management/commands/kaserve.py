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

from fle_utils.chronograph.models import Job
from fle_utils.config.models import Settings
from fle_utils.general import isnumeric
from fle_utils.internet.functions import get_ip_addresses
from kalite.caching import initialize_content_caches
from securesync.models import Device
import warnings
from kalite.shared.warnings import RemovedInKALite_v015_Warning


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
            default=os.path.join(settings.USER_DATA_ROOT, "runcherrypyserver.pid"),
            help="PID file"
        ),
        make_option(
            '--startup-lock-file',
            action='store',
            dest='startuplock',
            default=None,
            help="Remove this file after successful startup"
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
        initialize_content_caches()


    def handle(self, *args, **options):
        # Store base django settings and remove them from the options list
        # because we are proxying one type of option list to another format
        # where --foo=bar becomes foo=bar
        
        warnings.warn(
            "manage kaserve is deprecated, please use kalite start [--foreground] [...]",
            RemovedInKALite_v015_Warning
        )
        
        base_django_settings = {}
        for opt in BaseCommand.option_list:
            base_django_settings[opt.dest] = options[opt.dest]
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

        # In case any chronograph threads were interrupted the last time
        # the server was stopped, clear their is_running flags to allow
        # them to be started up again as needed.
        Job.objects.update(is_running=False)

        # Copy static media, one reason for not symlinking: It is not cross-platform and can cause permission issues
        # with many webservers
        logging.info("Copying static media...")
        call_command("collectstatic", interactive=False, verbosity=0)

        call_command("collectstatic_js_reverse", interactive=False)

        if options['startuplock']:
            os.unlink(options['startuplock'])
        
        # Now call the proper command
        if not options["production"]:
            call_command("runserver", "%s:%s" % (options["host"], options["port"]))
        else:
            del options["production"]
            addresses = get_ip_addresses(include_loopback=False)
            sys.stdout.write("To access KA Lite from another connected computer, try the following address(es):\n")
            for addr in addresses:
                sys.stdout.write("\thttp://%s:%s/\n" % (addr, settings.USER_FACING_PORT()))
            sys.stdout.write("To access KA Lite from this machine, try the following address:\n")
            sys.stdout.write("\thttp://127.0.0.1:%s/\n" % settings.USER_FACING_PORT())

            call_command("runcherrypyserver", *["%s=%s" % (key,val) for key, val in options.iteritems()], **base_django_settings)
