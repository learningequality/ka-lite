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


def call_command_subprocess(cmd, *args, **kwargs):
    assert "manage_py_dir" in kwargs, "don't forget to specify the manage_py_dir"
    manage_py_dir = kwargs["manage_py_dir"]
    del kwargs["manage_py_dir"]

    # Use sys to get the same executable running as is running this process.
    # Make sure to call the manage.py from this project.
    call_args = [sys.executable, os.path.join(manage_py_dir, "manage.py"), cmd]
    call_args += list(args)
    for key,val in kwargs.iteritems():
        call_args.append("--%s=%s" % (key, val))

    # We don't need to hold onto the process handle.
    #    we expect all commands to return eventually, on their own--
    #    we have no way to deal with a rogue process.
    # But, because they're subprocesses of this process, when the
    #    server stops, so do these processes.
    # Note that this is also OK because chronograph does all "stopping"
    #    using messaging through the database
    subprocess.Popen(call_args)




JOB_THREADS = {}

class CommandThread(threading.Thread):
    def __init__(self, cmd, *args, **kwargs):
        super(CommandThread, self).__init__()
        self.cmd = cmd
        self.args = args
        self.kwargs = kwargs

    def run(self):
        #logging.debug("Starting command %s with parameters %s, %s)" % (self.cmd, self.args, self.kwargs))
        call_command(self.cmd, *self.args, **self.kwargs)

def call_command_threaded(cmd, *args, **kwargs):
    global JOB_THREADS

    #logging.debug("Threaded launch of command %s with parameters %s, %s)" % (cmd, args, kwargs))
    if cmd in JOB_THREADS and JOB_THREADS[cmd].is_alive():
        pass#raise Exception(_("Command %(cmd)s is already currently running.  Please stop the previous job before trying to start.") % {"cmd": cmd})
    th = CommandThread(cmd=cmd, *args, **kwargs)
    th.start()
    JOB_THREADS[cmd] = th


def call_command_async(cmd, in_proc=True, *args, **kwargs):
    """
    Runs a manage.py command asynchronously, by calling into
    the subprocess module.

    This may be finicky, as it requires stringifying kwargs, but
    it works well for the current needs and should be safe for types
    that stringify in a way that commands can parse
    (which will work for str, bool, int, etc).
    """
    if in_proc:
        call_command_threaded(cmd, *args, **kwargs)
    else:
        call_command_subprocess(cmd, *args, **kwargs)


def call_outside_command_with_output(command, *args, **kwargs):
    """
    Runs call_command for a KA Lite installation at the given location,
    and returns the output.
    """
    assert "manage_py_dir" in kwargs, "don't forget to specify the manage_py_dir"
    manage_py_dir = kwargs["manage_py_dir"]
    del kwargs["manage_py_dir"]

    # build the command
    cmd = (sys.executable, os.path.join(manage_py_dir, "manage.py"), command)
    for arg in args:
        cmd += (arg,)
    for key, val in kwargs.items():
        key = key.replace(u"_",u"-")
        prefix = u"--" if command != "runcherrypyserver" else u""  # hack, but ... whatever!
        if isinstance(val, bool):
            cmd += (u"%s%s" % (prefix, key),)
        else:
            cmd += (u"%s%s=%s" % (prefix, key, unicode(val)),)

    # Execute the command, using subprocess/Popen
    cwd = os.getcwd()
    os.chdir(manage_py_dir)
    p = subprocess.Popen(cmd, shell=False, cwd=os.path.split(cmd[0])[0], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()
    os.chdir(cwd)

    # tuple output of stdout, stderr, and exit code
    return out + (1 if out[1] else 0,)


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