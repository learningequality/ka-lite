#!/usr/bin/env python

import logging, sys, os, signal, time, errno
from socket import gethostname
from django.core.management.base import BaseCommand
import django.contrib.admin
from django_cherrypy_wsgiserver import cherrypyserver

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
    'port': 8008,   # changed from 8088 to 8000 to follow django devserver default
    'threads': 50,
    'daemonize': False,
    'pidfile': None,
}

class Command(BaseCommand):
    help = "CherryPy Server for project. Requires CherryPy."
    args = "[various KEY=val options, use `runwsgiserver help` for help]"

    def handle(self, *args, **options):
        from django.conf import settings
        from django.utils import translation
        # Activate the current language, because it won't get activated later.
        try:
            translation.activate(settings.LANGUAGE_CODE)
        except AttributeError:
            pass
        runcherrypyserver(args)
        

def change_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    if not os.geteuid() == 0:
        # Do not try to change the gid/uid if not root.
        return
    (uid, gid) = get_uid_gid(uid, gid)
    os.setgid(gid)
    os.setuid(uid)

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
    First try SIGTERM and if it fails, SIGKILL. If process is still running, an exception is raised.
    """
    if os.path.exists(pidfile):
        pid = int(open(pidfile).read())
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError: #process does not exist
            os.remove(pidfile)
            return
        if poll_process(pid):
            #process didn't exit cleanly, make one last effort to kill it
            os.kill(pid, signal.SIGKILL)
            #if still_alive(pid):
            if poll_process(pid):
                raise OSError, "Process %s did not stop."
        os.remove(pidfile)


def runcherrypyserver(argset=[], **kwargs):
    # Get the options
    options = CPWSGI_OPTIONS.copy()
    options.update(kwargs)
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
        
    if "stop" in options:
        stop_server(options['pidfile'])
        return True
    
    cherrypyserver.run_cherrypy_server(**options)


if __name__ == '__main__':
    runcherrypyserver(sys.argv[1:])
