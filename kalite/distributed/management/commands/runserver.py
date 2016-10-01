from __future__ import print_function

import atexit
import os
import subprocess

from threading import Thread

from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand
from django.core.management.base import CommandError


class Command(RunserverCommand):
    """
    Subclass the RunserverCommand from Staticfiles to run browserify.
    """

    def __init__(self, *args, **kwargs):
        self.cleanup_closing = False
        self.browserify_process = None

        super(Command, self).__init__(*args, **kwargs)

    def handle(self, *args, **options):

        # We're subclassing runserver, which spawns threads for its
        # autoreloader with RUN_MAIN set to true, we have to check for
        # this to avoid running browserify twice.
        if not os.getenv('RUN_MAIN', False) and not getattr(self, "browserify_process"):

            browserify_thread = Thread(target=self.start_browserify)
            browserify_thread.daemon = True
            browserify_thread.start()

            atexit.register(self.kill_browserify_process)

        return super(Command, self).handle(*args, **options)

    def kill_browserify_process(self):
        if self.browserify_process.returncode is not None:
            return

        self.cleanup_closing = True
        self.stdout.write('Closing browserify process')

        self.browserify_process.terminate()

    def start_browserify(self):
        self.stdout.write('Starting browserify')

        self.browserify_process = subprocess.Popen(
            'node build.js --watch --debug',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=self.stdout,
            stderr=self.stderr)

        if self.browserify_process.poll() is not None:
            raise CommandError('Browserify failed to start')

        self.stdout.write('Browserify process on pid {0}'
                          .format(self.browserify_process.pid))

        self.browserify_process.wait()

        if self.browserify_process.returncode != 0 and not self.cleanup_closing:
            self.stdout.write(
                """
                ****************************************************************************
                Browserify exited unexpectedly - Javascript code will not be properly built.
                ****************************************************************************
                """)
