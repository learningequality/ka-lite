# -*- coding: utf-8 -*-
import imp
import os
import urlparse

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
        if getattr(settings, "CONTENT_ROOT", None):
            # Assessment items
            from kalite.contentload.settings import ASSESSMENT_ITEM_ROOT
            static_handler = cherrypy.tools.staticdir.handler(
                section="/",
                dir="",
                root=os.path.abspath(ASSESSMENT_ITEM_ROOT)
            )
            cherrypy.tree.mount(static_handler, settings.CONTENT_URL + "assessment/",)

            # Video content items
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

        # Serve the static files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.STATIC_ROOT)[1],
            root=os.path.abspath(os.path.split(settings.STATIC_ROOT)[0])
        )
        cherrypy.tree.mount(static_handler, settings.STATIC_URL)

        # Serve the static files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.CONTENT_DATA_PATH)[1],
            root=os.path.abspath(os.path.split(settings.CONTENT_DATA_PATH)[0])
        )
        cherrypy.tree.mount(static_handler, settings.CONTENT_DATA_URL)

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
            if fd:
                fd.close()
