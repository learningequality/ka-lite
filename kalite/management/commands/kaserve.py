"""
This is a command-line tool to execute functions helpful to testing.
"""
import os
import sys
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils.translation import ugettext as _

import settings
from config.models import Settings
from securesync.models import Device, Facility
from settings import LOG as logging
from utils.django_utils import call_command_with_output
from utils.general import isnumeric


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
            action='store_false',
            dest='run_in_proc',
            default=True,
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

        # Now call the proper command
        if options["run_in_proc"]:
            call_command("runserver", "%s:%s" % (options["host"], options["port"]))
        else:
            call_command("runcherrypyserver", *["%s=%s" % (key,val) for key, val in options.iteritems()])
