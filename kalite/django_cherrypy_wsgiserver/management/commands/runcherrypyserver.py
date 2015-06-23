#!/usr/bin/env python
import errno
import logging
import os
import signal
import socket
import sys
import time
from urllib import urlopen

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse

from ... import cherrypyserver
import warnings
from kalite.shared.warnings import RemovedInKALite_v015_Warning


CPWSGI_HELP = r"""
  Run this project in CherryPy's production quality http webserver.
  Note that it's called wsgiserver but it is actually a complete http server.

    runcherrypyserver [options] [cpwsgi settings] [stop]

Optional CherryPy server settings: (setting=value)
  host=HOSTNAME         hostname to listen on
                        Defaults to 127.0.0.1,
                        (set to 0.0.0.0 to bind all ip4 interfaces or :: for
                        all ip6 interfaces)
  port=PORTNUM          port to listen on
                        Defaults to 8000
  daemonize=BOOL        whether to detach from terminal
                        Defaults to False
  pidfile=FILE          write the spawned process-id to this file
  threads=NUMBER        Number of threads for server to use
  autoreload=BOOL       automatically reload the server if project modules change
                        defaults to False

Examples:
  Run a "standard" CherryPy wsgi server
    $ manage.py runcherrypyserver

  Run a CherryPy server on port 80
    $ manage.py runcherrypyserver port=80

  Run a CherryPy server as a daemon and write the spawned PID in a file
    $ manage.py runcherrypyserver daemonize=true pidfile=/var/run/django-cpwsgi.pid

"""

CPWSGI_OPTIONS = {
    'host': '127.0.0.1', # changed from localhost to avoid ip6 problem -clm
    'port': getattr(settings, "PRODUCTION_PORT", 8008),   # changed from 8088 to 8000 to follow django devserver default
    'threads': getattr(settings, "CHERRPY_THREAD_COUNT", 50),
    'daemonize': False,
    'pidfile': None,
    'autoreload': False,
}

class Command(BaseCommand):
    help = "CherryPy Server for project. Requires CherryPy."
    args = "[various KEY=val options, use `runcherrypyserver help` for help]"

    def handle(self, *args, **options):
        from django.conf import settings
        from django.utils import translation
        # Activate the current language, because it won't get activated later.
        try:
            translation.activate(settings.LANGUAGE_CODE)
        except AttributeError:
            pass
        runcherrypyserver(args)


# TODO(benjaoming):
# benjaoming: This doesn't work on Windows, but is replaced by functionality
# inside kalitectl so can be removed
def change_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    if hasattr(os, "geteuid") and not os.geteuid() == 0:
        # Do not try to change the gid/uid if not root.
        return
    (uid, gid) = get_uid_gid(uid, gid)
    os.setgid(gid)
    os.setuid(uid)


# TODO(benjaoming)(benjaoming):
# benjaoming: This doesn't work on Windows, but is replaced by functionality
# inside kalitectl so can be removed
def get_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    import pwd, grp
    uid, default_grp = pwd.getpwnam(uid)[2:4]
    if gid is None:
        gid = default_grp
    else:
        try:
            gid = grp.getgrnam(gid)[2]
        except KeyError:
            gid = default_grp
    return (uid, gid)


# TODO(benjaoming):
# benjaoming: This doesn't work on Windows, but is replaced by functionality
# inside kalitectl so can be removed
def poll_process(pid):
    """
    Poll for process with given pid up to 10 times waiting .25 seconds in between each poll.
    Returns False if the process no longer exists otherwise, True.
    """
    for n in range(10):
        time.sleep(0.25)
        try:
            # poll the process state
            os.kill(pid, 0)
        except OSError, e:
            if e[0] == errno.ESRCH:
                # process has died
                return False
            else:
                raise Exception
    return True


def stop_server(pidfile):
    """
    Stop process whose pid was written to supplied pidfile.
    """
    if os.path.exists(pidfile):
        try:
            with open(pidfile, "r") as fp:
                pid = int(fp.read())
            stop_server_using_pid(pid)
        except Exception as e:
            logging.warn("Error getting the PID and stopping the server: %s" % e)

        # if stop_server_using_pid did not raise an exception,
        #  we drop into the next line to remove the pidfile
        os.remove(pidfile)
    else:
        pass


def stop_server_using_pid(pid):
    """
    Stop process whose pid is supplied
    First try SIGTERM and if it fails, SIGKILL. If process is still running, an exception is raised.
    """
    logging.info("attempting to stop process %s" % pid)
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError: #process does not exist
        return
    if poll_process(pid):
        #process didn't exit cleanly, make one last effort to kill it
        os.kill(pid, signal.SIGKILL)
        #if still_alive(pid):
        if poll_process(pid):
            raise OSError, "Process %s did not stop."


def port_is_available(host, port):
    """
    Validates if the cherrypy server port is free;  This is needed in case the PID file
    for a currently running process does not exist or has the incorrect process ID recorded.
    """
    if int(port) < 1024 and hasattr(os, "geteuid") and os.geteuid() != 0:
        raise Exception("Port %s is less than 1024: you must be root to do this" % port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = socket.gethostbyname(host)
    result = sock.connect_ex((ip, int(port)))
    sock.close()
    if result != 0:
        logging.info("Port %s is available" % port)
        return True
    else:
        logging.warn("Port %s is busy" % port)
        return False


def ka_lite_is_using_port(host, port):
    """
    Tries the port with a /getpid/ url
    if there is a numeric response, that will be the pid of the cherrypyserver process
    This is needed in case the PID file has been deleted, but the server continues to run
    """

    pid = None

    try:
        pid = int(urlopen("http://%s:%s%s" % (host, port, reverse('getpid'))).read())
    except:
        try: # also try the old URL for getpid, since the running server may not be recent
            pid = int(urlopen("http://%s:%s%s" % (host, port, "/api/getpid")).read())
        except:
            pass

    if pid:
        logging.warn("Existing KA-Lite server found, PID %d" % pid)
        return pid


def runcherrypyserver(argset=[], **kwargs):
    # Get the options
    
    warnings.warn("runcherrypyserver() is deprecated", RemovedInKALite_v015_Warning)
    
    options = CPWSGI_OPTIONS.copy()
    options.update(kwargs)
    
    # TODO: What's going on here!? Care to comment, anonymous author? :)
    for x in argset:
        if "=" in x:
            k, v = x.split('=', 1)
        else:
            k, v = x, True
        if v=='False' or v=='false':
            v = False
        options[k.lower()] = v

    if "help" in options:
        print CPWSGI_HELP
        return
    
    # TODO(benjaoming): This is not in use anymore in `kalite stop` so can be deprecated
    if "stop" in options:
        warnings.warn("Using runcherrypyserver stop is deprecated, use `kalite stop`", DeprecationWarning)
        if options['pidfile']:
            stop_server(options['pidfile'])
            return True
        if options['host'] and options['port']:
            pid = ka_lite_is_using_port(options['host'], options['port'])
            stop_server_using_pid(pid)
            return True
        else:
            raise Exception("must have pidfile or host+port")

    if port_is_available(options['host'], options['port']):
        pass
    else:
        # TODO(benjaoming): Remove this
        # benjaoming: this is replaced by the stop command in kalitectl
        # existing_server_pid = ka_lite_is_using_port(options['host'], options['port'])
        # if existing_server_pid:
        #     stop_server_using_pid(existing_server_pid)
        #     # try again, is kalite still running on that port?
        #     time.sleep(5.0)
        #     existing_server_pid = ka_lite_is_using_port(options['host'], options['port'])
        #     if existing_server_pid:
        #         raise Exception("Existing kalite process cannot be stopped")
        raise Exception("Port %s is currently in use by another process, cannot continue" % options['port'])

        # if port_is_available(options['host'], options['port']):
        #    # Make a final check that the port is free.  This is needed in case someone downloaded
        #    #  and started another copy of KA Lite, and ran it with the default settings
        #    #  (port 8008, taken by Nginx), then it would kill the other server without
        #    # freeing up the port, so we need to raise an exception.
        #     pass
        # else:
        #     raise Exception("Port %s is currently in use by another process, cannot continue" % options['port'])

    if "stop" in options:
        #we are done, get out
        return True
    
    cherrypyserver.run_cherrypy_server(**options)


if __name__ == '__main__':
    runcherrypyserver(sys.argv[1:])
