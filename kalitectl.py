#!/usr/bin/env python
"""
KA Lite (Khan Academy Lite)

Supported by Foundation for Learning Equality
www.learningequality.org

Usage:
  kalite [options] [--skip-job-scheduler] start [DJANGO_OPTIONS ...]
  kalite [options] stop [DJANGO_OPTIONS ...]
  kalite [options] [--skip-job-scheduler] restart [DJANGO_OPTIONS ...]
  kalite [job-scheduler] status [options]
  kalite [options] shell [DJANGO_OPTIONS ...]
  kalite [options] test [DJANGO_OPTIONS ...]
  kalite [options] manage COMMAND [DJANGO_OPTIONS ...]
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
  --port=<arg>          A port number the server will listen on.
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
        os.path.join(os.environ['KALITE_DIR'], 'dist-packages'),
        os.path.join(os.environ['KALITE_DIR'], 'kalite')
    ] + sys.path
# KALITE_DIR not set, so called from some other source
else:
    filedir = os.path.dirname(__file__)
    sys.path = [os.path.join(filedir, 'python-packages'), os.path.join(filedir, 'kalite')] + sys.path


import httplib
import re
import subprocess

from threading import Thread
from docopt import docopt
from urllib2 import URLError
from socket import timeout

from django.core.management import ManagementUtility

from kalite.version import VERSION
from kalite.shared.compat import OrderedDict

# Necessary for loading default settings from kalite
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

# Where to store user data
KALITE_HOME = os.environ.get(
    "KALITE_HOME",
    os.path.join(os.path.expanduser("~"), ".kalite")
)
if not os.path.isdir(KALITE_HOME):
    os.mkdir(KALITE_HOME)
PID_FILE = os.path.join(KALITE_HOME, 'kalite.pid')
PID_FILE_JOB_SCHEDULER = os.path.join(KALITE_HOME, 'kalite_cronserver.pid')
STARTUP_LOCK = os.path.join(KALITE_HOME, 'kalite_startup.lock')

# if this environment variable is set, we activate the profiling machinery
PROFILE = os.environ.get("PROFILE")

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
        pid, port = int(open(filename, "r").read()), None
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
        pid, port = read_pid_file(PID_FILE)
    except (ValueError, OSError):
        raise NotRunning(100)  # Invalid PID file

    # PID file exists, but process is dead
    if not pid_exists(pid):
        if os.path.isfile(STARTUP_LOCK):
            raise NotRunning(6)  # Failed to start
        raise NotRunning(7)  # Unclean shutdown

    listen_port = port or LISTEN_PORT

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
    :param in_background: Creates a new process for the command
    """

    if not in_background:
        if PROFILE:
            profile_memory()

        utility = ManagementUtility([os.path.basename(sys.argv[0]), command] + args)
        # This ensures that 'kalite' is printed in help menus instead of
        # 'kalitectl.py' (a part from the top most text in `kalite manage help`
        utility.prog_name = 'kalite manage'
        utility.execute()
    else:
        # Create a new subprocess, beware that it won't die with the parent
        # so you have to kill it in another fashion

        # If we're on windows, we need to create a new process group, otherwise
        # the newborn will be murdered when the parent becomes a daemon
        if os.name == "nt":
            kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            kwargs = {}
        subprocess.Popen(
            [sys.executable, os.path.abspath(sys.argv[0]), "manage", command] + args,
            env=os.environ,
            **kwargs
        )


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
            pid, port = read_pid_file(STARTUP_LOCK)
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

    # Write current PID and optional port to a startup lock file
    with open(STARTUP_LOCK, "w") as f:
        f.write(str(os.getpid()))
        if os.environ.get("KALITE_LISTEN_PORT", None):
            f.write("\n" + os.environ["KALITE_LISTEN_PORT"])

    # Start the job scheduler (not Celery yet...)
    # This command is run before starting the server, in case the server
    # should be configured to not run in daemon mode or in case the
    # server fails to go to daemon mode.
    if not skip_job_scheduler:
        manage(
            'cronserver',
            in_background=True,
            args=update_default_args(
                ['--daemon', '--pid-file={0000:s}'.format(PID_FILE_JOB_SCHEDULER)],
                args
            )
        )
    args = update_default_args(
        [
            "--host=%s" % LISTEN_ADDRESS,
            "--daemonize",
            "--pidfile=%s" % PID_FILE,
            "--startup-lock-file=%s" % STARTUP_LOCK,
        ] + (["--production"] if not debug else []),
        args
    )
    manage('kaserve', args)


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
                pid, port = read_pid_file(PID_FILE)
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


def profile_memory():
    print("activating profile infrastructure.")

    import atexit
    import csv
    import resource
    import signal
    import sparkline
    import time

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

if __name__ == "__main__":
    arguments = docopt(__doc__, version=str(VERSION), options_first=True)

    if arguments['start']:
        if arguments["--port"]:
            os.environ["KALITE_LISTEN_PORT"] = arguments["--port"]
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
