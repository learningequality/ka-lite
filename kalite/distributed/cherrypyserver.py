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

# Due to #5140 (Windows XP doesn't know SVG), so we had to add this.
# Then because of #5233 we had to add a full mapping of all content types that
# we use.
WELL_KNOWN_CONTENT_TYPES = {
    "atom": "application/atom+xml",
    "json": "application/json",
    "jsonld": "application/ld+json",
    "rss": "application/rss+xml",
    "geojson": "application/vnd.geo+json",
    "rdf": "application/xml",
    "js": "application/javascript",
    "webmanifest": "application/manifest+json",
    "webapp": "application/x-web-app-manifest+json",
    "appcache": "text/cache-manifest",
    "mid": "audio/midi",
    "aac": "audio/mp4",
    "mp3": "audio/mpeg",
    "oga": "audio/ogg",
    "ra": "audio/x-realaudio",
    "wav": "audio/x-wav",
    "bmp": "image/bmp",
    "gif": "image/gif",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "svg": "image/svg+xml",
    "tif": "image/tiff",
    "wbmp": "image/vnd.wap.wbmp",
    "webp": "image/webp",
    "jng": "image/x-jng",
    "3gp": "video/3gpp",
    "f4p": "video/mp4",
    "mpeg": "video/mpeg",
    "ogv": "video/ogg",
    "mov": "video/quicktime",
    "webm": "video/webm",
    "flv": "video/x-flv",
    "mng": "video/x-mng",
    "asf": "video/x-ms-asf",
    "wmv": "video/x-ms-wmv",
    "avi": "video/x-msvideo",
    "cur": "image/x-icon",
    "doc": "application/msword",
    "xls": "application/vnd.ms-excel",
    "ppt": "application/vnd.ms-powerpoint",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "woff": "application/font-woff",
    "woff2": "application/font-woff2",
    "eot": "application/vnd.ms-fontobject",
    "ttc": "application/x-font-ttf",
    "otf": "font/opentype",
    "ear": "application/java-archive",
    "hqx": "application/mac-binhex40",
    "bin": "application/octet-stream",
    "pdf": "application/pdf",
    "ai": "application/postscript",
    "rtf": "application/rtf",
    "kml": "application/vnd.google-earth.kml+xml",
    "kmz": "application/vnd.google-earth.kmz",
    "wmlc": "application/vnd.wap.wmlc",
    "7z": "application/x-7z-compressed",
    "bbaw": "application/x-bb-appworld",
    "torrent": "application/x-bittorrent",
    "crx": "application/x-chrome-extension",
    "cco": "application/x-cocoa",
    "jardiff": "application/x-java-archive-diff",
    "jnlp": "application/x-java-jnlp-file",
    "run": "application/x-makeself",
    "oex": "application/x-opera-extension",
    "pl": "application/x-perl",
    "pdb": "application/x-pilot",
    "rar": "application/x-rar-compressed",
    "rpm": "application/x-redhat-package-manager",
    "sea": "application/x-sea",
    "swf": "application/x-shockwave-flash",
    "sit": "application/x-stuffit",
    "tcl": "application/x-tcl",
    "crt": "application/x-x509-ca-cert",
    "xpi": "application/x-xpinstall",
    "xhtml": "application/xhtml+xml",
    "xsl": "application/xslt+xml",
    "zip": "application/zip",
    "css": "text/css",
    "htm": "text/html",
    "mml": "text/mathml",
    "txt": "text/plain",
    "vcard": "text/vcard",
    "xloc": "text/vnd.rim.location.xloc",
    "jad": "text/vnd.sun.j2me.app-descriptor",
    "wml": "text/vnd.wap.wml",
    "vtt": "text/vtt",
    "htc": "text/x-component",
}

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
                root=os.path.abspath(ASSESSMENT_ITEM_ROOT),
                content_types=WELL_KNOWN_CONTENT_TYPES,
            )
            cherrypy.tree.mount(static_handler, settings.CONTENT_URL + "assessment/",)

            # Video content items
            static_handler = cherrypy.tools.staticdir.handler(
                section="/",
                dir=os.path.split(settings.CONTENT_ROOT)[1],
                root=os.path.abspath(os.path.split(settings.CONTENT_ROOT)[0]),
                content_types=WELL_KNOWN_CONTENT_TYPES,
            )
            cherrypy.tree.mount(static_handler, settings.CONTENT_URL)

        # Serve the static media files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.MEDIA_ROOT)[1],
            root=os.path.abspath(os.path.split(settings.MEDIA_ROOT)[0]),
            content_types=WELL_KNOWN_CONTENT_TYPES,
        )
        cherrypy.tree.mount(static_handler, settings.MEDIA_URL)

        # Serve the static files
        static_handler = cherrypy.tools.staticdir.handler(
            section="/",
            dir=os.path.split(settings.STATIC_ROOT)[1],
            root=os.path.abspath(os.path.split(settings.STATIC_ROOT)[0]),
            content_types=WELL_KNOWN_CONTENT_TYPES,
        )
        cherrypy.tree.mount(static_handler, settings.STATIC_URL)

        # Serve the static admin media. From django's internal (django.core.servers.basehttp)
        admin_static_dir = os.path.join(django.__path__[0], 'contrib', 'admin', 'static')
        admin_static_handler = cherrypy.tools.staticdir.handler(
            section='/',
            dir='admin',
            root=admin_static_dir,
            content_types=WELL_KNOWN_CONTENT_TYPES,
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
