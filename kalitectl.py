#!/usr/bin/env python
"""
KA Lite (Khan Academy Lite)

Supported by Foundation for Learning Equality
www.learningequality.org

Usage:
  kalite start [options] [--skip-job-scheduler] [DJANGO_OPTIONS ...]
  kalite stop [options] [DJANGO_OPTIONS ...]
  kalite setting SETTING_NAME
  kalite restart [options] [--skip-job-scheduler] [DJANGO_OPTIONS ...]
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

Examples:
  kalite start          Start kalite
  kalite url            Tell me where kalite is available from
  kalite status         How is kalite doing?
  kalite stop           Stop kalite again
  kalite shell          Display a Django shell
  kalite manage help    Show the Django management usage dialogue

Planned features:
  kalite start --foreground   Run kalite in the foreground and do not go to
                              daemon mode.
  kalite diagnose             Outputs user and copy-paste friendly diagnostics
  kalite query [COMMAND ...]  A query method for external UIs etc. to send
                              commands and obtain data from kalite.
  
  Universal --verbose option and --debug option. Shows INFO level and DEBUG
  level from logging.. depends on proper logging being introduced and
  settings.LOGGERS. Currently, --debug just tells cherrypy to do "debug" mode.

"""
from __future__ import print_function
# Add distributed python-packages subfolder to current path
# DO NOT IMPORT BEFORE THIS LIKE
import sys
import os

# KALITE_DIR set, so probably called from bin/kalite
if 'KALITE_DIR' in os.environ:
    sys.path = [
        os.path.join(os.environ['KALITE_DIR'], 'python-packages'),
        os.path.join(os.environ['KALITE_DIR'], 'kalite')
    ] + sys.path
# KALITE_DIR not set, so called from some other source
else:
    sys.path = ['python-packages', 'kalite'] + sys.path


from django.core.management import ManagementUtility, get_commands
from threading import Thread
from docopt import docopt
import httplib
from urllib2 import URLError
from socket import timeout
from kalite.version import VERSION

if os.name == "nt":
    from subprocess import Popen, CREATE_NEW_PROCESS_GROUP

# Necessary for loading default settings from kalite
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

KALITE_HOME = os.path.join(os.path.expanduser("~"), ".kalite")
if not os.path.isdir(KALITE_HOME):
    os.mkdir(KALITE_HOME)
PID_FILE = os.path.join(KALITE_HOME, 'kalite.pid')
PID_FILE_JOB_SCHEDULER = os.path.join(KALITE_HOME, 'kalite_cronserver.pid')
STARTUP_LOCK = os.path.join(KALITE_HOME, 'kalite_startup.lock')

# TODO: Currently, this address might be hard-coded elsewhere, too
LISTEN_ADDRESS = "0.0.0.0"
# TODO: Can be configured in django settings which is really odd because that's
# run INSIDE the http server
LISTEN_PORT = 8008
# TODO: Hard coded, not good. It's because we currently cannot load up the
# django environment, see #2890
PING_URL = '/api/cherrypy/getpid'

# Status codes for kalite, might be refactored into kalite package itself
# for easier access to outside processes
STATUS_RUNNING = 0
STATUS_STOPPED = 1
STATUS_STARTING_UP = 4
STATUS_NOT_RESPONDING = 5
STATUS_FAILED_TO_START = 6
STATUS_UNCLEAN_SHUTDOWN = 7
STATUS_UNKNOWN_INSTANCE = 8
STATUS_SERVER_CONFIGURATION_ERROR = 9
STATUS_PID_FILE_READ_ERROR = 99
STATUS_PID_FILE_INVALID = 100
STATUS_UNKNOW = 101


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
        import ctypes
        PROCESS_TERMINATE = 1
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)  # @UndefinedVariable
        ctypes.windll.kernel32.TerminateProcess(handle, -1)  # @UndefinedVariable
        ctypes.windll.kernel32.CloseHandle(handle)  # @UndefinedVariable


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
    :returns: (PID of running server, address, port)
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
    conn = httplib.HTTPConnection("127.0.0.1", listen_port, timeout=3)
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
        # Not a valid INT was returned, so probably not KA Lite
        raise NotRunning(8)

    if pid == pid:
        return pid, LISTEN_ADDRESS, listen_port  # Correct PID !
    else:
        # Not the correct PID, maybe KA Lite is running from somewhere else!
        raise NotRunning(8)

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
        utility = ManagementUtility([os.path.basename(sys.argv[0]), self.command] + self.args)
        # This ensures that 'kalite' is printed in help menus instead of
        # 'kalitectl.py' (a part from the top most text in `kalite manage help`
        utility.prog_name = 'kalite manage'
        utility.execute()


def manage(command, args=[], in_background=False):
    """
    Run a django command on the kalite project

    :param command: The django command string identifier, e.g. 'runserver'
    :param args: List of options to parse to the django management command
    :param in_background: Creates a sub-process for the command
    """
    # Ensure that django.core.management's global _command variable is set
    # before call commands, especially the once that run in the background
    get_commands()
    # Import here so other commands can run faster
    if not in_background:
        utility = ManagementUtility([os.path.basename(sys.argv[0]), command] + args)
        # This ensures that 'kalite' is printed in help menus instead of
        # 'kalitectl.py' (a part from the top most text in `kalite manage help`
        utility.prog_name = 'kalite manage'
        utility.execute()
    else:
        if os.name != "nt":
            thread = ManageThread(command, args=args, name=" ".join([command]+args))
            thread.start()
        else:
            # TODO (aron): for versions > 0.13, see if we can just have everyone spawn another process (Popen vs. ManageThread)
            Popen([sys.executable, os.path.abspath(sys.argv[0]), "manage", command] + args, creationflags=CREATE_NEW_PROCESS_GROUP)


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
                sys.stderr.write(
                    "Refusing to start: Start up lock exists: {0:s}\n".format(STARTUP_LOCK))
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
    # This command is run before starting the server, in case the server
    # should be configured to not run in daemon mode or in case the
    # server fails to go to daemon mode.
    if not skip_job_scheduler:
        manage(
            'cronserver',
            in_background=True,
            args=[
                '--daemon', '--pid-file={0000:s}'.format(PID_FILE_JOB_SCHEDULER)]
        )
    args = "--host={host:s} --daemonize{production:s} --pidfile={pid:s} --startup-lock-file={startup:s}".format(
        host=LISTEN_ADDRESS,
        pid=PID_FILE,
        production=" --production" if not debug else "",
        startup=STARTUP_LOCK,
    )
    manage('kaserve', args=args.split(" "))


def setting(setting_name):
    import kalite.settings
    print(kalite.settings.package_selected(setting_name))

def stop(args=[], sys_exit=True):
    """
    Stops the kalite server, either from PID or through a management command

    :param args: List of options to parse to the django management command
    :raises: NotRunning
    """

    # Kill the KA lite server
    try:
        kill_pid(get_pid()[0])
        os.unlink(PID_FILE)
    # Handle exceptions of kalite not already running
    except NotRunning as e:
        sys.stderr.write(
            "Already stopped. Status was: {000:s}\n".format(status.codes[e.status_code]))
        # Indicates if kalite instance was found and then killed with force
        killed_with_force = False
        if e.status_code == STATUS_NOT_RESPONDING:
            sys.stderr.write(
                "Not responding, killing with force\n"
            )
            try:
                f = open(PID_FILE, "r")
                pid = int(f.read())
                kill_pid(pid)
                killed_with_force = True
            except ValueError:
                sys.stderr.write("Could not find PID in .pid file\n")
            except OSError:  # TODO: More specific exception handling
                sys.stderr.write("Could not read .pid file\n")
        if not killed_with_force:
            if sys_exit:
                sys.exit(-1)
            return  # Do not continue because error could not be handled

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
            sys.stderr.write(
                "Invalid job scheduler PID file: {00:s}".format(PID_FILE_JOB_SCHEDULER))

    sys.stderr.write("kalite stopped\n")
    if sys_exit:
        sys.exit(0)


def status():
    """
    Check the server's status. For possible statuses, see the status dictionary
    status.codes

    :returns: status_code, key has description in status.codes
    """
    try:
        __, __, port = get_pid()
        sys.stderr.write("{msg:s} (0)\n".format(msg=status.codes[0]))
        sys.stderr.write("KA Lite running on:\n\n")
        from fle_utils.internet.functions import get_ip_addresses
        for addr in get_ip_addresses():
            sys.stderr.write("\thttp://%s:%s/\n" % (addr, port))
        return 0
    except NotRunning as e:
        status_code = e.status_code
        verbose_status = status.codes[status_code]
        sys.stderr.write("{msg:s} ({code:d})\n".format(
            code=status_code, msg=verbose_status))
        return status_code
status.codes = {
    STATUS_RUNNING: 'OK, running',
    STATUS_STOPPED: 'Stopped',
    STATUS_STARTING_UP: 'Starting up',
    STATUS_NOT_RESPONDING: 'Not responding',
    STATUS_FAILED_TO_START: 'Failed to start (check logs)',
    STATUS_UNCLEAN_SHUTDOWN: 'Unclean shutdown',
    STATUS_UNKNOWN_INSTANCE: 'Unknown KA Lite running on port',
    STATUS_SERVER_CONFIGURATION_ERROR: 'KA Lite server configuration error',
    STATUS_PID_FILE_READ_ERROR: 'Could not read PID file',
    STATUS_PID_FILE_INVALID: 'Invalid PID file',
    STATUS_UNKNOW: 'Could not determine status',
}


def url():
    """
    Check the server's status. For possible statuses, see the status dictionary
    status.codes

    :returns: status_code, key has description in status.codes
    """
    try:
        get_pid()
        sys.stderr.write()
        status_code = 0
    except NotRunning as e:
        status_code = e.status_code
    verbose_status = status.codes[status_code]
    sys.stderr.write("{msg:s} ({code:d})\n".format(
        code=status_code, msg=verbose_status))
    return status_code


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
    0: 'OK, running',
    1: 'Stopped',
    99: 'Could not read PID file',
    100: 'Invalid PID file',
}


if __name__ == "__main__":
    arguments = docopt(__doc__, version=str(VERSION), options_first=True)

    if arguments['start']:
        start(
            debug=arguments['--debug'],
            skip_job_scheduler=arguments['--skip-job-scheduler'],
            args=arguments['DJANGO_OPTIONS']
        )

    elif arguments['stop']:
        stop(args=arguments['DJANGO_OPTIONS'])

    elif arguments['restart']:
        stop(args=arguments['DJANGO_OPTIONS'], sys_exit=False)
        start(
            debug=arguments['--debug'],
            skip_job_scheduler=arguments['--skip-job-scheduler'],
            args=arguments['DJANGO_OPTIONS']
        )

    elif arguments['setting']:
        setting(setting_name=arguments['SETTING_NAME'])

    elif arguments['status']:
        if arguments['job-scheduler']:
            status_code = status_job_scheduler()
            verbose_status = status_job_scheduler.codes[status_code]
        else:
            status_code = status()
        sys.exit(status_code)

    elif arguments['shell']:
        manage('shell', args=arguments['DJANGO_OPTIONS'])

    elif arguments['test']:
        manage('test', args=arguments['DJANGO_OPTIONS'])

    elif arguments['manage']:
        command = arguments['COMMAND']
        manage(command, args=arguments['DJANGO_OPTIONS'])
