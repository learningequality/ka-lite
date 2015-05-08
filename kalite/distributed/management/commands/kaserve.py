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
from fle_utils.internet.functions import get_ip_addresses
from kalite.caching import initialize_content_caches
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
        make_option(
            '--use-inotify',
            action='store_true',
            dest='use_inotify',
            default=(sys.platform == 'linux2'),
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

        # In case any chronograph threads were interrupted the last time
        # the server was stopped, clear their is_running flags to allow
        # them to be started up again as needed.
        Job.objects.update(is_running=False)

        call_command("collectstatic", interactive=False)

        if options['startuplock']:
            os.unlink(options['startuplock'])

        # Now call the proper command
        if not options["production"]:

            if options['use_inotify']:
                self.inject_inotify_reloader()

            call_command("runserver", "%s:%s" % (options["host"], options["port"]))
        else:
            del options["production"]
            del options['use_inotify']
            sys.stdout.write("To access KA Lite from another connected computer, try the following address(es):\n")
            for addr in get_ip_addresses():
                sys.stdout.write("\thttp://%s:%s/\n" % (addr, settings.USER_FACING_PORT()))
            call_command("runcherrypyserver", *["%s=%s" % (key,val) for key, val in options.iteritems()])

    def inject_inotify_reloader(self):
        """A function that replaces django.utils.autoreload.reloader_thread's
        stat based reloading to a function that uses the Linux inotify API.

        This is meant to be a drop-in replacement for reloader_thread,
        which means that it must conform to its API (as of Django
        1.5). That means on every detected code change, it must exit
        with return code 3. The parent thread should then handle the
        actual reloading of modules.

        """

        from django.utils import autoreload
        import pyinotify

        class _EventHandler(pyinotify.ProcessEvent):

            def process_IN_MODIFY(self, event):
                print "modified %s, restarting" % event.pathname
                sys.exit(3)

        def inotify_reloader_thread():
            """
            Watch for file modifications using inotify. If a file modification
            is detected, exit with ret code 3.

            """
            autoreload.ensure_echo_on()

            watcher = pyinotify.WatchManager()
            notifier = pyinotify.Notifier(watcher, _EventHandler())

            filenames = [getattr(m, "__file__", None) for m in sys.modules.values()]
            for filename in filter(None, filenames):
                if filename.endswith(".pyc") or filename.endswith(".pyo"):
                    filename = filename[:-1]
                if filename.endswith("$py.class"):
                    filename = filename[:-9] + ".py"
                if not os.path.exists(filename):
                    # File might be in an egg, so it can't be reloaded.
                    continue

                watcher.add_watch(filename, pyinotify.IN_MODIFY)

            notifier.loop()

        autoreload.reloader_thread = inotify_reloader_thread
