#!/usr/bin/env python
"""
KA Lite (Khan Academy Lite)

Supported by Foundation for Learning Equality
www.learningequality.org

Usage:
  kalite start [--foreground --watch] [options] [DJANGO_OPTIONS ...]
  kalite stop [options] [DJANGO_OPTIONS ...]
  kalite restart [options] [DJANGO_OPTIONS ...]
  kalite status [options]
  kalite shell [options] [DJANGO_OPTIONS ...]
  kalite test [options] [DJANGO_OPTIONS ...]
  kalite manage [options] COMMAND [DJANGO_OPTIONS ...]
  kalite diagnose [options]
  kalite -h | --help
  kalite --version

Options:
  -h --help             Show this screen.
  --version             Show version.
  COMMAND               The name of any available django manage command. For
                        help, type `kalite manage help`
  --debug               Output debug messages (for development)
  --port=<arg>          Use a non-default port on which to start the HTTP server
                        or to query an existing server (stop/status)
  --settings=<arg>      Specify Django's settings module. Must follow python's
                        import syntax.
  --skip-job-scheduler  KA Lite runs a so-called "cronograph", it's own built-in
                        automatic job scheduler required for downloading videos
                        and sync'ing with online sources. If you don't need this
                        you can skip it!
  DJANGO_OPTIONS        All options are passed on to the django manage command.
                        Notice that all django options must appear *last* and
                        should not be mixed with other options. Only long-name
                        options ('--long-name') are supported.

Examples:
  kalite start          Start KA Lite
  kalite url            Tell me where KA Lite is available from
  kalite status         How is KA Lite doing?
  kalite stop           Stop KA Lite
  kalite shell          Display a Django shell
  kalite manage help    Show the Django management usage dialogue
  kalite diagnose       Show system information for debugging

  kalite start --foreground   Run kalite in the foreground and do not go to
                              daemon mode.
  kalite start --watch      Set cherrypy to watch for changes to Django code and start
                            the Watchify process to recompile Javascript dynamically.

Planned features:
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
import atexit
import subprocess
import platform
import os
import socket
import sys
import time
import traceback

# KALITE_DIR set, so probably called from bin/kalite
if 'KALITE_DIR' in os.environ:
    sys.path = [
        os.path.join(os.environ['KALITE_DIR'], 'python-packages'),
        os.path.join(os.environ['KALITE_DIR'], 'dist-packages'),
        os.path.join(os.environ['KALITE_DIR'], 'kalite')
    ] + sys.path
# KALITE_DIR not set, so called from some other source
else:
    filedir = os.path.dirname(__file__)
    sys.path = [os.path.join(filedir, 'python-packages'), os.path.join(filedir, 'kalite')] + sys.path

if sys.version_info >= (3,):
    sys.stderr.write("Detected incompatible Python version %s.%s.%s\n" % sys.version_info[:3])
    sys.stderr.write("Please set the KALITE_PYTHON environment variable to a Python 2.7 interpreter.\n")
    sys.exit(1)

import httplib
import re
import cherrypy

# We do not understand --option value, only --option=value.
# Match all patterns of "--option value" and fail if they exist
__validate_cmd_options = re.compile(r"--?[^\s]+\s+(?:(?!--|-[\w]))")
if __validate_cmd_options.search(" ".join(sys.argv[1:])):
    sys.stderr.write("Please only use --option=value or -x123 patterns. No spaces allowed between option and value. The option parser gets confused if you do otherwise.\n\nWill be fixed for next version 0.15")
    sys.exit(1)

from threading import Thread
from docopt import DocoptExit, printable_usage, parse_defaults, \
    parse_pattern, formal_usage, parse_argv, TokenStream, Option, AnyOptions, \
    extras, Dict
from urllib2 import URLError
from socket import timeout

from django.core.management import ManagementUtility, get_commands

import kalite
from kalite.django_cherrypy_wsgiserver.cherrypyserver import DjangoAppPlugin
from kalite.shared.compat import OrderedDict
from fle_utils.internet.functions import get_ip_addresses

# Environment variables that are used by django+kalite
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.project.settings.default")
os.environ.setdefault("KALITE_HOME", os.path.join(os.path.expanduser("~"), ".kalite"))
os.environ.setdefault("KALITE_LISTEN_PORT", "8008")

# Where to store user data
KALITE_HOME = os.environ["KALITE_HOME"]
SERVER_LOG = os.path.join(KALITE_HOME, "server.log")

if not os.path.isdir(KALITE_HOME):
    os.mkdir(KALITE_HOME)
PID_FILE = os.path.join(KALITE_HOME, 'kalite.pid')
NODE_PID_FILE = os.path.join(KALITE_HOME, 'kalite_node.pid')

STARTUP_LOCK = os.path.join(KALITE_HOME, 'kalite_startup.lock')

# if this environment variable is set, we activate the profiling machinery
PROFILE = os.environ.get("PROFILE")

# TODO: Currently, this address might be hard-coded elsewhere, too
LISTEN_ADDRESS = "0.0.0.0"
# TODO: Can be configured in django settings which is really odd because that's
# run INSIDE the http server
DEFAULT_LISTEN_PORT = os.environ.get("KALITE_LISTEN_PORT")
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


def update_default_args(defaults, updates):
    """
    Takes a list of default arguments and overwrites the defaults with
    contents of updates.

    e.g.:

    update_default_args(["--somearg=default"], ["--somearg=overwritten"])
     => ["--somearg=overwritten"]

    This is done to avoid defining all known django command line arguments,
    we just want to proxy things and update with our own default values without
    looking into django.
    """
    # Returns either the default or an updated argument
    arg_name = re.compile(r"^-?-?\s*=?([^\s=-]+)")
    # Create a dictionary of defined defaults and updates where '-somearg' is
    # always the key, update the defined defaults dictionary with the updates
    # dictionary thus overwriting the defaults.
    defined_defaults_ = map(
        lambda arg: (arg_name.search(arg).group(1), arg),
        defaults
    )
    # OrderedDict because order matters when space-split options such as "-v 2"
    # cause arguments to span over severel elements.
    defined_defaults = OrderedDict()
    for elm in defined_defaults_:
        defined_defaults[elm[0]] = elm[1]
    defined_updates_ = map(
        lambda arg: (arg_name.search(arg).group(1), arg),
        updates
    )
    defined_updates = OrderedDict()
    for elm in defined_updates_:
        defined_updates[elm[0]] = elm[1]
    defined_defaults.update(defined_updates)
    return defined_defaults.values()


def get_size(start_path):
    """Utility function, returns the size (bytes) of a folder"""
    total_size = 0
    for dirpath, __, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


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


def read_pid_file(filename):
    """
    Reads a pid file and returns the contents. Pid files have 1 or 2 lines; the first line is always the pid, and the
    optional second line is the port the server is listening on.

    :param filename: Filename to read
    :return: the tuple (pid, port) with the pid in the file and the port number if it exists. If the port number doesn't
        exist, then port is None.
    """
    try:
        pid, port = open(filename, "r").readlines()
        pid, port = int(pid), int(port)
    except ValueError:
        # The file only had one line
        try:
            pid, port = int(open(filename, "r").read()), None
        except ValueError:
            pid, port = None, None
    return pid, port


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
                pid, port = read_pid_file(STARTUP_LOCK)
                # Does the PID in there still exist?
                if pid_exists(pid):
                    raise NotRunning(STATUS_STARTING_UP)
                # It's dead so assuming the startup went badly
                else:
                    raise NotRunning(STATUS_FAILED_TO_START)
            # Couldn't parse to int
            except TypeError:
                raise NotRunning(STATUS_STOPPED)
        raise NotRunning(STATUS_STOPPED)  # Stopped

    # PID file exists, check if it is running
    try:
        pid, port = read_pid_file(PID_FILE)
    except (ValueError, OSError):
        raise NotRunning(STATUS_PID_FILE_INVALID)  # Invalid PID file

    # PID file exists, but process is dead
    if not pid_exists(pid):
        if os.path.isfile(STARTUP_LOCK):
            raise NotRunning(STATUS_FAILED_TO_START)  # Failed to start
        raise NotRunning(STATUS_UNCLEAN_SHUTDOWN)  # Unclean shutdown

    listen_port = port or DEFAULT_LISTEN_PORT

    # Timeout is 1 second, we don't want the status command to be slow
    conn = httplib.HTTPConnection("127.0.0.1", listen_port, timeout=3)
    try:
        conn.request("GET", PING_URL)
        response = conn.getresponse()
    except timeout:
        raise NotRunning(STATUS_NOT_RESPONDING)
    except (httplib.HTTPException, URLError):
        if os.path.isfile(STARTUP_LOCK):
            raise NotRunning(STATUS_STARTING_UP)  # Starting up
        raise NotRunning(STATUS_UNCLEAN_SHUTDOWN)

    if response.status == 404:
        raise NotRunning(STATUS_UNKNOWN_INSTANCE)  # Unknown HTTP server

    if response.status != 200:
        # Probably a mis-configured KA Lite
        raise NotRunning(STATUS_SERVER_CONFIGURATION_ERROR)

    try:
        pid = int(response.read())
    except ValueError:
        # Not a valid INT was returned, so probably not KA Lite
        raise NotRunning(STATUS_UNKNOWN_INSTANCE)

    if pid == pid:
        return pid, LISTEN_ADDRESS, listen_port  # Correct PID !
    else:
        # Not the correct PID, maybe KA Lite is running from somewhere else!
        raise NotRunning(STATUS_UNKNOWN_INSTANCE)

    raise NotRunning(STATUS_UNKNOW)  # Could not determine


class ManageThread(Thread):

    def __init__(self, command, *args, **kwargs):
        self.command = command
        self.args = kwargs.pop('args', [])
        super(ManageThread, self).__init__(*args, **kwargs)
        self.setDaemon(True)

    def run(self):
        utility = ManagementUtility([os.path.basename(sys.argv[0]), self.command] + self.args)
        # This ensures that 'kalite' is printed in help menus instead of
        # 'kalitectl.py' (a part from the top most text in `kalite manage help`
        utility.prog_name = 'kalite manage'
        utility.execute()


def manage(command, args=[], as_thread=False):
    """
    Run a django command on the kalite project

    :param command: The django command string identifier, e.g. 'runserver'
    :param args: List of options to parse to the django management command
    :param as_thread: Runs command in thread and returns immediately
    """

    args = update_default_args(["--traceback"], args)

    if not as_thread:
        if PROFILE:
            profile_memory()

        utility = ManagementUtility([os.path.basename(sys.argv[0]), command] + args)
        # This ensures that 'kalite' is printed in help menus instead of
        # 'kalitectl.py' (a part from the top most text in `kalite manage help`
        utility.prog_name = 'kalite manage'
        utility.execute()
    else:
        get_commands()  # Needed to populate the available commands before issuing one in a thread
        thread = ManageThread(command, args=args, name=" ".join([command] + args))
        thread.start()
        return thread


# Watchify running code modified from:
# https://github.com/beaugunderson/django-gulp/blob/master/django_gulp/management/commands/runserver.py

def start_watchify():
    sys.stdout.write('Starting watchify')

    watchify_process = subprocess.Popen(
        args='node build.js --debug --watch --staticfiles',
        shell=True,
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr)

    if watchify_process.poll() is not None:
        raise RuntimeError('watchify failed to start')

    print('Started watchify process on pid {0}'.format(
        watchify_process.pid))

    with open(NODE_PID_FILE, 'w') as f:
        f.write("%d" % watchify_process.pid)

    atexit.register(kill_watchify_process)

def kill_watchify_process():
    pid, __ = read_pid_file(NODE_PID_FILE)
    # PID file exists, but process is dead
    if not pid_exists(pid):
        print('watchify process not running')
    else:
        kill_pid(pid)
        os.unlink(NODE_PID_FILE)
        sys.stdout.write('watchify process killed')


def start(debug=False, watch=False, daemonize=True, args=[], skip_job_scheduler=False, port=None):
    """
    Start the kalite server as a daemon

    :param args: List of options to parse to the django management command
    :param port: Non-default port to bind to. You cannot run kalite on
                 multiple ports at the same time.
    :param daemonize: Default True, will run in foreground if False
    :param skip_job_scheduler: Skips running the job scheduler in a separate thread
    """
    # TODO: Do we want to fail if running as root?

    port = int(port or DEFAULT_LISTEN_PORT)

    if not daemonize:
        sys.stderr.write("Running 'kalite start' in foreground...\n")
    else:
        sys.stderr.write("Running 'kalite start' as daemon (system service)\n")

    sys.stderr.write("\nStand by while the server loads its data...\n\n")

    if os.path.exists(STARTUP_LOCK):
        try:
            pid, __ = read_pid_file(STARTUP_LOCK)
            # Does the PID in there still exist?
            if pid_exists(pid):
                sys.stderr.write(
                    "Refusing to start: Start up lock exists: {0:s}\n".format(STARTUP_LOCK))
                sys.stderr.write("Remove the file and try again.\n")
                sys.exit(1)
        # Couldn't parse to int
        except TypeError:
            pass

        os.unlink(STARTUP_LOCK)

    try:
        if get_pid():
            sys.stderr.write("Refusing to start: Already running\n")
            sys.stderr.write("Use 'kalite stop' to stop the instance.\n")
            sys.exit(1)
    except NotRunning:
        pass

    # Check that the port is available by creating a simple socket and see
    # if it succeeds... if it does, the port is occupied.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection_error = sock.connect_ex(('127.0.0.1', port))
    if not connection_error:
        sys.stderr.write(
            "Port {0} is occupied. Please close the process that is using "
            "it.\n".format(port)
        )
        sys.exit(1)

    # Write current PID and optional port to a startup lock file
    with open(STARTUP_LOCK, "w") as f:
        f.write("%s\n%d" % (str(os.getpid()), port))

    manage('initialize_kalite')

    if watch:
        watchify_thread = Thread(target=start_watchify)
        watchify_thread.daemon = True
        watchify_thread.start()

    # Remove the startup lock at this point
    if STARTUP_LOCK:
        os.unlink(STARTUP_LOCK)

    # Print output to user about where to find the server
    addresses = get_ip_addresses(include_loopback=False)
    print("To access KA Lite from another connected computer, try the following address(es):")
    for addr in addresses:
        print("\thttp://%s:%s/" % (addr, port))
    print("To access KA Lite from this machine, try the following address:")
    print("\thttp://127.0.0.1:%s/\n" % port)

    # Daemonize at this point, no more user output is needed
    if daemonize:

        from django.utils.daemonize import become_daemon
        kwargs = {}
        # Truncate the file
        open(SERVER_LOG, "w").truncate()
        print("Going to daemon mode, logging to {0}".format(SERVER_LOG))
        kwargs['out_log'] = SERVER_LOG
        kwargs['err_log'] = SERVER_LOG
        become_daemon(**kwargs)
        # Write the new PID
        with open(PID_FILE, 'w') as f:
            f.write("%d\n%d" % (os.getpid(), port))

    # Start the job scheduler (not Celery yet...)
    cron_thread = None
    if not skip_job_scheduler:
        cron_thread = manage(
            'cronserver_blocking',
            args=[],
            as_thread=True
        )

    # Start cherrypy service
    cherrypy.config.update({
        'server.socket_host': LISTEN_ADDRESS,
        'server.socket_port': port,
        'server.thread_pool': 18,
        'checker.on': False,
    })

    DjangoAppPlugin(cherrypy.engine).subscribe()
    if not watch:
        # cherrypyserver automatically reloads if any modules change
        # Switch-off that functionality here to save cpu cycles
        # http://docs.cherrypy.org/stable/appendix/faq.html
        cherrypy.engine.autoreload.unsubscribe()

    try:
        cherrypy.quickstart()
    except KeyboardInterrupt:
        # Handled in cherrypy by waiting for all threads to join
        pass
    except SystemExit:
        print("KA Lite caught system exit signal, quitting.")

    print("FINISHED serving HTTP")

    if cron_thread:
        # Do not exit thread together with the main process, let it finish
        # cleanly
        print("Asking KA Lite job scheduler to terminate...")
        from fle_utils.chronograph.management.commands import cronserver_blocking
        cronserver_blocking.shutdown = True
        cron_thread.join()
        print("Job scheduler terminated.")


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
                pid, __ = read_pid_file(PID_FILE)
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

    sys.stderr.write("kalite stopped\n")
    if sys_exit:
        sys.exit(0)


def get_urls():
    """
    Fetch a list of urls
    :returns: STATUS_CODE, ['http://abcd:1234', ...]
    """
    try:
        __, __, port = get_pid()
        urls = []
        for addr in get_ip_addresses():
            urls.append("http://{}:{}/".format(addr, port))
        return STATUS_RUNNING, urls
    except NotRunning as e:
        return e.status_code, []


def get_urls_proxy():
    """
    Get addresses of the server if we're using settings.PROXY_PORT

    :raises: Exception for sure if django.conf.settings isn't loaded
    """
    # Import settings and check if a proxy port exists
    from django.conf import settings
    if hasattr(settings, 'PROXY_PORT') and settings.PROXY_PORT:
        sys.stderr.write(
            "\nKA Lite configured behind another server, primary "
            "addresses are:\n\n"
        )
        for addr in get_ip_addresses():
            yield "http://{}:{}/".format(addr, settings.PROXY_PORT)


def status():
    """
    Check the server's status. For possible statuses, see the status dictionary
    status.codes

    Status *always* outputs the current status in the first line if stderr.
    The following lines contain optional information such as the addresses where
    the server is listening.

    :returns: status_code, key has description in status.codes
    """
    status_code, urls = get_urls()

    if status_code == STATUS_RUNNING:
        sys.stderr.write("{msg:s} (0)\n".format(msg=status.codes[0]))
        sys.stderr.write("KA Lite running on:\n\n")
        for addr in urls:
            sys.stderr.write("\t{}\n".format(addr))
        # Import settings and check if a proxy port exists
        try:
            for addr in get_urls_proxy():
                sys.stderr.write("\t{}\n".format(addr))
        except Exception as e:
            sys.stderr.write(
                "\n\nWarning, exception fetching KA Lite settings module:\n\n" +
                str(e) + "\n\n"
            )
        return STATUS_RUNNING
    else:
        verbose_status = status.codes[status_code]
        sys.stderr.write("{msg:s} ({code:d})\n".format(
            code=status_code, msg=verbose_status))
        return status_code
status.codes = {
    STATUS_RUNNING: 'OK, running',
    STATUS_STOPPED: 'Stopped',
    STATUS_STARTING_UP: 'Starting up',
    STATUS_NOT_RESPONDING: 'Not responding',
    STATUS_FAILED_TO_START: 'Failed to start (check log file: {0})'.format(SERVER_LOG),
    STATUS_UNCLEAN_SHUTDOWN: 'Unclean shutdown',
    STATUS_UNKNOWN_INSTANCE: 'Unknown KA Lite running on port',
    STATUS_SERVER_CONFIGURATION_ERROR: 'KA Lite server configuration error',
    STATUS_PID_FILE_READ_ERROR: 'Could not read PID file',
    STATUS_PID_FILE_INVALID: 'Invalid PID file',
    STATUS_UNKNOW: 'Could not determine status',
}


def diagnose():
    """
    This command diagnoses an installation of KA Lite

    It has to be able to work with instances of KA Lite that users do not
    actually own, however it's assumed that the path and the 'kalite' commands
    are configured and work.

    The function is currently non-robust, meaning that not all aspects of
    diagnose data collection is guaranteed to succeed, thus the command could
    potentially fail :(

    Example: KALITE_HOME=/home/otheruser/.kalite kalite diagnose --port=7007
    """

    print("")
    print("KA Lite diagnostics")
    print("")

    # Tell users we are calculating, because checking the size of the
    # content directory is slow. Flush immediately after.
    print("Calculating diagnostics...")
    sys.stdout.flush()
    print("")

    # Key, value store for diagnostics
    # Not using OrderedDict because of python 2.6
    diagnostics = []

    diag = lambda x, y: diagnostics.append((x, y))

    diag("KA Lite version", kalite.__version__)
    diag("python", sys.version)
    diag("platform", platform.platform())

    status_code, urls = get_urls()
    for addr in urls:
        diag("server address", addr)
    for addr in get_urls_proxy():
        diag("server proxy", addr)

    diag("server status", status.codes[status_code])

    settings_imported = True  # Diagnostics from settings
    try:
        from django.conf import settings
        from django.template.defaultfilters import filesizeformat
    except:
        settings_imported = False
        diag("Settings failure", traceback.format_exc())

    if settings_imported:
        diag("installed in", os.path.dirname(kalite.__file__))
        diag("content root", settings.CONTENT_ROOT)
        diag("content size", filesizeformat(get_size(settings.CONTENT_ROOT)))
        diag("user database", settings.DATABASES['default']['NAME'])
        diag("assessment database", settings.DATABASES['assessment_items']['NAME'])
        try:
            from securesync.models import Device
            device = Device.get_own_device()
            sync_sessions = device.client_sessions.all()
            zone = device.get_zone()
            diag("device name", str(device.name))
            diag("device ID", str(device.id))
            diag("device registered", str(device.is_registered()))
            diag("synced", str(sync_sessions.latest('timestamp').timestamp if sync_sessions.exists() else "Never"))
            diag("sync result", ("OK" if sync_sessions.latest('timestamp').errors == 0 else "Error") if sync_sessions.exists() else "-")
            diag("zone ID", str(zone.id) if zone else "Unset")
        except:
            diag("Device failure", traceback.format_exc())

    for k, v in diagnostics:

        # Pad all the values to match the key column
        values = str(v).split("\n")
        values = "\n".join([values[0]] + map(lambda x: (" " * 22) + x, values[1:]))

        print((k.upper() + ": ").ljust(21), values)


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


def profile_memory():
    print("activating profile infrastructure.")

    import csv
    import resource  # @UnresolvedImport
    import signal
    import sparkline

    starttime = time.time()

    mem_usage = []

    def print_results():
        try:
            highest_mem_usage = next(s for s in sorted(mem_usage, key=lambda x: x['mem_usage'], reverse=True))
        except StopIteration:
            highest_mem_usage = {"pid": os.getpid(), "timestamp": 0, "mem_usage": 0}

        graph = sparkline.sparkify([m['mem_usage'] for m in mem_usage]).encode("utf-8")

        print("PID: {pid} Highest memory usage: {mem_usage}MB. Usage over time: {sparkline}".format(sparkline=graph, **highest_mem_usage))

    def write_profile_results(filename=None):

        if not filename:
            filename = os.path.join(os.getcwd(), "memory_profile.log")

        with open(filename, "w") as f:
            si_es_vi = csv.DictWriter(f, ["pid", "timestamp", "mem_usage"])
            si_es_vi.writeheader()
            for _, content in enumerate(mem_usage):
                si_es_vi.writerow(content)

    def handle_exit():
        write_profile_results()
        print_results()

    def collect_mem_usage(_sig, _frame):
        """
        Callback for when we get a SIGPROF from the kernel. When called,
        we record the time and memory usage.
        """
        pid = os.getpid()
        m = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        curtime = time.time() - starttime
        mem_usage.append({"pid": pid, "timestamp": curtime, "mem_usage": m / 1024})

    signal.setitimer(signal.ITIMER_PROF, 1, 1)

    signal.signal(signal.SIGPROF, collect_mem_usage)
    atexit.register(handle_exit)


# TODO(benjaoming): When this PR is merged, we can stop this crazyness
# https://github.com/docopt/docopt/pull/283
def docopt(doc, argv=None, help=True, version=None, options_first=False):  # @ReservedAssignment help
    """Re-implementation of docopt.docopt() function to parse ANYTHING at
    the end (for proxying django options)."""
    if argv is None:
        argv = sys.argv[1:]

    DocoptExit.usage = printable_usage(doc)
    options = parse_defaults(doc)
    pattern = parse_pattern(formal_usage(DocoptExit.usage), options)
    argv = parse_argv(TokenStream(argv, DocoptExit), list(options),
                      options_first)
    pattern_options = set(pattern.flat(Option))
    for ao in pattern.flat(AnyOptions):
        doc_options = parse_defaults(doc)
        ao.children = list(set(doc_options) - pattern_options)
    extras(help, version, argv, doc)
    __matched, __left, collected = pattern.fix().match(argv)

    # if matched and left == []:  # better error message if left?
    if collected:  # better error message if left?
        result = Dict((a.name, a.value) for a in (pattern.flat() + collected))
        collected_django_options = len(result.get('DJANGO_OPTIONS', []))
        result['DJANGO_OPTIONS'] = (
            result.get('DJANGO_OPTIONS', []) +
            sys.argv[len(collected) + (collected_django_options or 1):]
        )
        # If any of the collected arguments are also in the DJANGO_OPTIONS,
        # then exit because we don't want users to have put options for kalite
        # at the end of the command
        if any(map(lambda x: x.name in map(lambda x: x.split("=")[0], result['DJANGO_OPTIONS']), collected)):
            sys.stderr.write(
                "Cannot mix django manage command options with kalite options. "
                "Always put django management options last.\n\n"
            )
            raise DocoptExit()
        return result
    raise DocoptExit()


if __name__ == "__main__":
    # Since positional arguments should always come first, we can safely
    # replace " " with "=" to make options "--xy z" same as "--xy=z".
    arguments = docopt(__doc__, version=str(kalite.__version__), options_first=False)

    settings_module = arguments.pop('--settings', None)
    if settings_module:
        os.environ['DJANGO_SETTINGS_MODULE'] = settings_module

    if arguments['start']:
        start(
            debug=arguments['--debug'],
            watch=arguments['--watch'],
            skip_job_scheduler=arguments['--skip-job-scheduler'],
            args=arguments['DJANGO_OPTIONS'],
            daemonize=not arguments['--foreground'],
            port=arguments["--port"]
        )

    elif arguments['stop']:
        stop(args=arguments['DJANGO_OPTIONS'])

    elif arguments['restart']:
        stop(args=arguments['DJANGO_OPTIONS'], sys_exit=False)
        # add a short sleep to ensure port is freed before we try starting up again
        time.sleep(1)
        start(
            debug=arguments['--debug'],
            skip_job_scheduler=arguments['--skip-job-scheduler'],
            args=arguments['DJANGO_OPTIONS'],
            port=arguments["--port"]
        )

    elif arguments['status']:
        status_code = status()
        sys.exit(status_code)

    elif arguments['diagnose']:
        diagnose()

    elif arguments['shell']:
        manage('shell', args=arguments['DJANGO_OPTIONS'])

    elif arguments['test']:
        manage('test', args=arguments['DJANGO_OPTIONS'])

    elif arguments['manage']:
        command = arguments['COMMAND']
        manage(command, args=arguments['DJANGO_OPTIONS'])
