# -*- coding: utf-8 -*-
import imp
import os, sys, time, signal, errno
import urlparse

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../../kalite/"

sys.path = [PROJECT_PATH, os.path.join(PROJECT_PATH, "../"), os.path.join(PROJECT_PATH, "../python-packages/")] + sys.path

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

import cherrypy
from cherrypy.process import plugins

import django
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

__all__ = ['DjangoAppPlugin']

class DjangoAppPlugin(plugins.SimplePlugin):
    def __init__(self, bus):
        """ CherryPy engine plugin to configure and mount
        the Django application onto the CherryPy server.
        """
        plugins.SimplePlugin.__init__(self, bus)

    def start(self):
        """ When the bus starts, the plugin is also started
        and we load the Django application. We then mount it on
        the CherryPy engine for serving as a WSGI application.
        We let CherryPy serve the application's static files.
        """
        cherrypy.log("Loading and serving the Django application")
        cherrypy.tree.graft(WSGIHandler())

        # Serve the content files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.CONTENT_ROOT)[1],
            root=os.path.abspath(os.path.split(settings.CONTENT_ROOT)[0])
        )
        cherrypy.tree.mount(static_handler, settings.CONTENT_URL)

        # Serve the static media files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.MEDIA_ROOT)[1],
            root=os.path.abspath(os.path.split(settings.MEDIA_ROOT)[0])
        )
        cherrypy.tree.mount(static_handler, settings.MEDIA_URL)

        # Serve the static admin media. From django's internal (django.core.servers.basehttp)
        admin_static_dir = os.path.join(django.__path__[0], 'contrib', 'admin', 'static')
        admin_static_handler = cherrypy.tools.staticdir.handler(
            section='/',
            dir='admin',
            root=admin_static_dir
        )
        cherrypy.tree.mount(admin_static_handler, urlparse.urljoin(settings.STATIC_URL, 'admin'))

    def load_settings(self):
        """ Loads the Django application's settings. You can
        override this method to provide your own loading
        mechanism. Simply return an instance of your settings module.
        """
        
        name = os.environ['DJANGO_SETTINGS_MODULE']
        package, mod = name.rsplit('.', 1)
        fd, path, description = imp.find_module(mod, [package.replace('.', '/')])

        try:
            return imp.load_module(mod, fd, path, description)
        finally:
            if fd: fd.close()

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


def run_cherrypy_server(host="127.0.0.1", port=8008, threads=50, daemonize=False, pidfile=None, autoreload=False):
    
    if daemonize:
        if not pidfile:
            pidfile = '~/cpwsgi_%d.pid' % port
        stop_server(pidfile)

        from django.utils.daemonize import become_daemon
        become_daemon()

        fp = open(pidfile, 'w')
        fp.write("%d\n" % os.getpid())
        fp.close()
    
    cherrypy.config.update({
        'server.socket_host': host,
        'server.socket_port': int(port),
        'server.thread_pool': int(threads),
        'checker.on': False,
    })
    
    DjangoAppPlugin(cherrypy.engine).subscribe()
    if not autoreload:
        # cherrypyserver automatically reloads if any modules change
        # Switch-off that functionality here to save cpu cycles
        # http://docs.cherrypy.org/stable/appendix/faq.html
        cherrypy.engine.autoreload.unsubscribe()

    cherrypy.quickstart()
    if pidfile:
        stop_server(pidfile)
    
if __name__=="__main__":
        
    run_cherrypy_server()