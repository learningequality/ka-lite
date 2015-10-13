"""
This module is for developing kalite!

Use it like this for instance:

   kalite manage runserver --settings=kalite.project.settings.dev

You can also write you own settings module my_settings.py, example:

from kalite.project.settings.dev import *

ANOTHER_SETTING = "le blah"

And then from the directory containing your settings module:

   kalite manage runserver --settings=my_settings

"""
from .base import *  # @UnusedWildImport

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TASTYPIE_FULL_DEBUG = True

# Set logging level based on the value of DEBUG (evaluates to 0 if False,
# 1 if True)
LOG = logging.getLogger("kalite")
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

SECURESYNC_PROTOCOL = "http"
CENTRAL_SERVER_HOST = "staging.%s" % CENTRAL_SERVER_DOMAIN
CENTRAL_SERVER_URL = "%s://%s" % (SECURESYNC_PROTOCOL, CENTRAL_SERVER_HOST)

# Force DeprecationWarning to show in DEBUG
if DEBUG:
    warnings.simplefilter('error', DeprecationWarning)


INSTALLED_APPS += [
    'django_snippets',  # used in contact form and (debug) profiling middleware
    'debug_toolbar',
]
TEMPLATE_CONTEXT_PROCESSORS += [
    'django.core.context_processors.debug',  # used in conjunction with toolbar to show query information
]
MIDDLEWARE_CLASSES += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'fle_utils.django_utils.middleware.JsonAsHTML'
]

#######################################
# DEBUG TOOLBAR
#######################################

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',  # This belongs to DISABLE_PANELS by default
)

DEBUG_TOOLBAR_CONFIG = {
    'ENABLE_STACKTRACES': True,
}

CACHES["default"] = {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'unique-snowflake',
    'TIMEOUT': 24 * 60 * 60  # = 24 hours
}
