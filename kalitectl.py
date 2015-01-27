#!/usr/bin/env python
"""
KA Lite (Khan Academy Lite)

Supported by Foundation for Learning Equality
www.learningequality.org

Usage:
  kalite start [options] [--skip-job-scheduler] [DJANGO_OPTIONS ...]
  kalite stop [options] [DJANGO_OPTIONS ...]
  kalite status [job-scheduler] [options]
  kalite shell [options] [DJANGO_OPTIONS ...]
  kalite test [options] [DJANGO_OPTIONS ...]
  kalite manage COMMAND [options] [DJANGO_OPTIONS ...]
  kalite -h | --help
  kalite --version

Options:
  -h --help             Show this screen.
  --version             Show version.
  COMMAND               The name of any available django manage command. For
                        help, type `kalite manage help`
  --debug               Output debug messages (for development)
  --skip-job-scheduler  For `kalite start`: Skips running the job scheduler
                        (useful for dev)
  DJANGO_OPTIONS        All options are passed on to the django manage command.
                        Notice that all django options must be place *last* and
                        should not be mixed with other options.
"""
from __future__ import print_function
# Add distributed python-packages subfolder to current path
# DO NOT IMPORT BEFORE THIS LIKE
import sys
sys.path = ['python-packages', 'kalite'] + sys.path

from django.core.management import execute_from_command_line
from threading import Thread
from docopt import docopt
import httplib
from urllib2 import URLError
from socket import timeout
from kalite.version import VERSION
import os

# Necessary for loading default settings from kalite
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

KALITE_HOME = os.path.join(os.path.expanduser("~"), ".kalite")
if not os.path.isdir(KALITE_HOME):
    os.mkdir(KALITE_HOME)
PID_FILE = os.path.join(KALITE_HOME, 'kalite.pid')
PID_FILE_JOB_SCHEDULER = os.path.join(KALITE_HOME, 'kalite_cronserver.pid')
STARTUP_LOCK = os.path.join(KALITE_HOME, 'kalite_startup.lock')

# TODO
# Currently, this address might be hard-coded elsewhere, too
LISTEN_ADDRESS = "0.0.0.0"
# Can be configured in django settings which is really odd because that's run INSIDE the http server
LISTEN_PORT = 8008
# Hard coded, not good. It's because we currently cannot load up the django environment, see #2890
PING_URL = '/api/cherrypy/getpid'


class NotRunning(Exception):
    """
    Raised when server was expected to run, but didn't. Contains a status
    code explaining why.
    """
    
    def __init__(self, status_code):
        self.status_code = status_code
        super(NotRunning, self).__init__()


# Utility functions for pinging or killing PIDs
if os.name == 'posix':
    def pid_exists(pid):
        """Check whether PID exists in the current process table."""
        import errno
        if pid < 0:
            return False
        try:
            # Send signal 0, this is harmless
            os.kill(pid, 0)
        except OSError as e:
            return e.errno == errno.EPERM
        else:
            return True
    
    def kill_pid(pid):
        """Kill a PID by sending a posix signal"""
        import signal
        try:
            os.kill(pid, signal.SIGTERM)
        # process does not exist
        except OSError:
            return
        # process didn't exit cleanly, make one last effort to kill it
        if pid_exists(pid):
            os.kill(pid, signal.SIGKILL)

else:
    def pid_exists(pid):
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x100000

        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        if process != 0:
            kernel32.CloseHandle(process)
            return True
        else:
            return False
    
    def kill_pid(pid):
        """Kill the proces using pywin32 and pid"""
        import win32api  # @UnresolvedImport
        PROCESS_TERMINATE = 1
        handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
        win32api.TerminateProcess(handle, -1)
        win32api.CloseHandle(handle)


def get_pid():
    """
    Tries to get the PID of a server.
    
    TODO: This function has for historical reasons maintained to try to get
    the PID of a KA Lite server without a PID file running on the same port.
    The behavior is to make an HTTP request for the PID on a certain port.
    This behavior is stupid, because a KA lite process may just be part of a
    process pool, so it won't be able to tell the correct PID for sure,
    anyways.
    The behavior is also quite redundant given that `kalite start` should always
    create a PID file, and if its been started directly with the runserver
    command, then its up to the developer to know what's happening.
    :returns: PID of running server
    :raises: NotRunning
    """
    
    # There is no PID file (created by server daemon)
    if not os.path.isfile(PID_FILE):
        # Is there a startup lock?
        if os.path.isfile(STARTUP_LOCK):
            try:
                pid = int(open(STARTUP_LOCK).read())
                # Does the PID in there still exist?
                if pid_exists(pid):
                    raise NotRunning(4)
                # It's dead so assuming the startup went badly
                else:
                    raise NotRunning(6)
            # Couldn't parse to int
            except TypeError:
                raise NotRunning(1)
        raise NotRunning(1)  # Stopped
    
    # PID file exists, check if it is running
    try:
        pid = int(open(PID_FILE, "r").read())
    except (ValueError, OSError):
        raise NotRunning(100)  # Invalid PID file
    
    # PID file exists, but process is dead
    if not pid_exists(pid):
        if os.path.isfile(STARTUP_LOCK):
            raise NotRunning(6)  # Failed to start
        raise NotRunning(7)  # Unclean shutdown

    # TODO: why is the port in django settings!? :) /benjaoming
    from django.conf import settings
    listen_port = getattr(settings, "CHERRYPY_PORT", LISTEN_PORT)
    
    # Timeout is 1 second, we don't want the status command to be slow
    conn = httplib.HTTPConnection(LISTEN_ADDRESS, listen_port, timeout=1)
    try:
        conn.request("GET", PING_URL)
        response = conn.getresponse()
    except timeout:
        raise NotRunning(5)
    except (httplib.HTTPException, URLError):
        if os.path.isfile(STARTUP_LOCK):
            raise NotRunning(4)  # Starting up
        raise NotRunning(7)
    
    if response.status == 404:
        raise NotRunning(8)  # Unknown HTTP server
    
    if response.status != 200:
        raise NotRunning(9)  # Probably a mis-configured KA Lite
    
    try:
        pid = int(response.read())
    except ValueError:
        raise NotRunning(8)  # Not a valid INT was returned, so probably not KA Lite
    
    if pid == pid:
        return pid  # Correct PID !
    else:
        raise NotRunning(8)  # Not the correct PID, maybe KA Lite is running from somewhere else!
    
    raise NotRunning(101)  # Could not determine


class ManageThread(Thread):
    """
    Runs a command in the background
    """
    daemon = True
    
    def __init__(self, command, *args, **kwargs):
        self.command = command
        self.args = kwargs.pop('args', [])
        return super(ManageThread, self).__init__(*args, **kwargs)

    def run(self):
        execute_from_command_line(
            [os.path.basename(sys.argv[0]), self.command] + self.args
        )


def manage(command, args=[], in_background=False):
    """
    Run a django command on the kalite project
    
    :param command: The django command string identifier, e.g. 'runserver'
    :param args: List of options to parse to the django management command
    :param in_background: Creates a sub-process for the command
    """
    # Import here so other commands can run faster
    if not in_background:
        execute_from_command_line(
            [os.path.basename(sys.argv[0]), command] + args
        )
    else:
        thread = ManageThread(command, args=args)
        thread.start()
    

def start(debug=False, args=[], skip_job_scheduler=False):
    """
    Start the kalite server as a daemon

    :param args: List of options to parse to the django management command
    """
    # TODO: Check if PID_FILE exists and if it is still running. If it still
    # runs then die.
    
    # TODO: Make sure that we are not root!
    
    # TODO: What does not the production=true actually do and how can we
    # control the log level and which log files to write to
    
    if os.path.exists(STARTUP_LOCK):
        try:
            pid = int(open(STARTUP_LOCK).read())
            # Does the PID in there still exist?
            if pid_exists(pid):
                sys.stderr.write("Refusing to start: Start up lock exists: {:s}\n".format(STARTUP_LOCK))
                sys.exit(1)
        # Couldn't parse to int
        except TypeError:
            pass
        
        os.unlink(STARTUP_LOCK)
    
    try:
        if get_pid():
            sys.stderr.write("Refusing to start: Already running\n")
            sys.exit(1)
    except NotRunning:
        pass
    
    # Write current PID to a startup lock file
    with open(STARTUP_LOCK, "w") as f:
        f.write(str(os.getpid()))
    
    # Start the job scheduler (not Celery yet...)
    if not skip_job_scheduler:
        manage(
            'cronserver',
            in_background=True,
            args=['--daemon', '--pid-file={:s}'.format(PID_FILE_JOB_SCHEDULER)]
        )
    args = "--host={host:s} --daemonize{production:s} --pidfile={pid:s} --startup-lock-file={startup:s}".format(
        host=LISTEN_ADDRESS,
        pid=PID_FILE,
        production=" --production" if not debug else "",
        startup=STARTUP_LOCK,
    )
    manage('kaserve', args=args.split(" "))


def stop(args=[]):
    """
    Stops the kalite server, either from PID or through a management command

    :param args: List of options to parse to the django management command
    :raises: NotRunning
    """
    
    # Kill the KA lite server
    try:
        kill_pid(get_pid())
        os.unlink(PID_FILE)
    except NotRunning as e:
        sys.stderr.write("Already stopped. Status was: {:s}\n".format(status.codes[e.status_code]))
        return

    # If there's no PID for the job scheduler, just quit
    if not os.path.isfile(PID_FILE_JOB_SCHEDULER):
        pass
    else:
        try:
            pid = int(open(PID_FILE_JOB_SCHEDULER, 'r').read())
            if pid_exists(pid):
                kill_pid(pid)
            os.unlink(PID_FILE_JOB_SCHEDULER)
        except (ValueError, OSError):
            sys.stderr.write("Invalid job scheduler PID file: {:s}".format(PID_FILE_JOB_SCHEDULER))
    
    print("kalite stopped")


def status():
    """
    Check the server's status. For possible statuses, see the status dictionary
    status.codes
    
    :returns: status_code, key has description in status.codes
    """
    try:
        get_pid()
        return 0
    except NotRunning as e:
        return e.status_code
status.codes = {
    0: 'Running',
    1: 'Stopped',
    4: 'Starting up',
    5: 'Not responding',
    6: 'Failed to start (check logs)',
    7: 'Unclean shutdown',
    8: 'Unknown KA Lite running on port',
    9: 'KA Lite server configuration error',
    99: 'Could not read PID file',
    100: 'Invalid PID file',
    101: 'Could not determine status',
}


def status_job_scheduler():
    """Returns the status of the cron server"""
    if not os.path.isfile(PID_FILE_JOB_SCHEDULER):
        return 1
    try:
        pid_exists(int(open(PID_FILE_JOB_SCHEDULER, 'r').read()))
        return 1
    except ValueError:
        return 100
    except OSError:
        return 99
status_job_scheduler.codes = {
    0: 'Running',
    1: 'Stopped',
    99: 'Could not read PID file',
    100: 'Invalid PID file',
}


if __name__ == "__main__":
    arguments = docopt(__doc__, version=str(VERSION), options_first=True)
    
    if arguments['start']:
        start(debug=arguments['--debug'], args=arguments['DJANGO_OPTIONS'])
    
    elif arguments['stop']:
        stop(args=arguments['DJANGO_OPTIONS'])
    
    elif arguments['status']:
        if arguments['job-scheduler']:
            status_code = status_job_scheduler()
            verbose_status = status_job_scheduler.codes[status_code]
        else:
            status_code = status()
            verbose_status = status.codes[status_code]
        sys.stderr.write("{:d} {}\n".format(status_code, verbose_status))
        sys.exit(status_code)
    
    elif arguments['shell']:
        manage('shell', args=arguments['DJANGO_OPTIONS'])
    
    elif arguments['test']:
        manage('test', args=arguments['DJANGO_OPTIONS'])
    
    elif arguments['manage']:
        command = arguments['COMMAND']
        manage(command, args=arguments['DJANGO_OPTIONS'])
