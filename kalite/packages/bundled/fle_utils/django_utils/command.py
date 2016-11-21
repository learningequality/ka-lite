import multiprocessing
import os
import re
import subprocess
import sys
import threading
from cStringIO import StringIO
from optparse import make_option

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import translation
from django.utils.translation import ugettext as _


def call_command_with_output(cmd, *args, **kwargs):
    """
    Run call_command while capturing stdout/stderr and calls to sys.exit
    """

    backups = [sys.stdout, sys.stderr, sys.exit]
    try:
        sys.stdout = StringIO()     # capture output
        sys.stderr = StringIO()
        sys.exit = lambda exit_code: sys.stderr.write("Exit code: %d" % exit_code) if exit_code else ""

        call_command(cmd, *args, **kwargs)

        out = sys.stdout.getvalue() # release output
        err = sys.stderr.getvalue() # release err

        # parse off exit code from stderr
        match = re.match(r".*Exit code: ([0-9]+)$", err.replace("\n",""), re.M)
        if match is None:
            val = 0
        else:
            val = int(match.groups()[0])

            # Having trouble regexp-ing with newlines :(  Here's my hacky solution
            match = re.match(r"^(.*)__newline__Exit code: [0-9]+$", err.replace("\n", "__newline__"), re.M)
            assert match is not None
            err = match.groups()[0].replace("__newline__", "\n")

        return (out,err, val)

    finally:
        sys.stdout = backups[0]
        sys.stderr = backups[1]
        sys.exit   = backups[2]


class CommandProcess(multiprocessing.Process):
    def __init__(self, cmd, *args, **kwargs):
        super(CommandProcess, self).__init__()
        self.cmd = cmd
        self.args = args
        self.kwargs = kwargs

    def run(self):
        call_command(self.cmd, *self.args, **self.kwargs)


class CommandThread(threading.Thread):
    def __init__(self, cmd, *args, **kwargs):
        super(CommandThread, self).__init__()
        self.cmd = cmd
        self.args = args
        self.kwargs = kwargs

    def run(self):
        #logging.debug("Starting command %s with parameters %s, %s)" % (self.cmd, self.args, self.kwargs))
        call_command(self.cmd, *self.args, **self.kwargs)


JOB_THREADS = {}
def call_command_subprocess(cmd, *args, **kwargs):
    p = CommandProcess(cmd, *args, **kwargs)
    p.start()
    return p


def call_command_threaded(cmd, *args, **kwargs):
    global JOB_THREADS

    #logging.debug("Threaded launch of command %s with parameters %s, %s)" % (cmd, args, kwargs))
    if cmd in JOB_THREADS and JOB_THREADS[cmd].is_alive():
        pass#raise Exception(_("Command %(cmd)s is already currently running.  Please stop the previous job before trying to start.") % {"cmd": cmd})
    th = CommandThread(cmd, *args, **kwargs)
    th.start()
    JOB_THREADS[cmd] = th
    return th


def call_command_async(cmd, *args, **kwargs):
    """
    Runs a manage.py command asynchronously, by calling into
    the subprocess module.

    This may be finicky, as it requires stringifying kwargs, but
    it works well for the current needs and should be safe for types
    that stringify in a way that commands can parse
    (which will work for str, bool, int, etc).
    """
    #  Workaround for #3704. It seems like running cron for downloading videos
    # as a different thread on the same process in OS X results in a normal exit.
    # That's it, the kalite executable just quits, no segfaults or anything.
    # The workaround for now is to spawn subprocesses by default on OS X,
    # and have everyone else spawn threads.
    is_osx = sys.platform == 'darwin'
    in_proc = kwargs.pop('in_proc', not is_osx)
    
    if in_proc:
        return call_command_threaded(cmd, *args, **kwargs)
    else:

        # Let's use the OS's python interpreter.
        return call_command_subprocess(cmd, *args, **kwargs)


class LocaleAwareCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--locale',
            action='store',
            dest='locale',
            default=settings.LANGUAGE_CODE,
            help='Locale (translation) for command output',  # when I localized this, I got an error...
            metavar="LANG_CODE"),
    )

    def execute(self, *args, **kwargs):
        """Set the language up before execute calls into handle.
        Better to do this way, so subclasses aren't forced to call
        into a superclass handle function"""
        saved_import_settings = self.can_import_settings
        self.can_import_settings = False  # HACK to force Django (with their unusually unoverridable decision to hard-code setting en-us)

        self.locale = kwargs["locale"]
        translation.activate(self.locale)

        super(LocaleAwareCommand, self).execute(*args, **kwargs)

        # Aaaaand back to normal.
        self.can_import_settings = saved_import_settings
