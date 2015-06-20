from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Set logging level based on the value of DEBUG (evaluates to 0 if False,
# 1 if True)
LOGGING_LEVEL = getattr()
LOG = logging.getLogger("kalite")
LOG.setLevel(logging.DEBUG)
logging.basicConfig()

SECURESYNC_PROTOCOL = "http"
CENTRAL_SERVER_HOST = "staging.%s" % CENTRAL_SERVER_DOMAIN
CENTRAL_SERVER_URL = "%s://%s" % (SECURESYNC_PROTOCOL, CENTRAL_SERVER_HOST)

# Force DeprecationWarning to show in DEBUG
if DEBUG:
    warnings.simplefilter('error', DeprecationWarning)


INSTALLED_APPS += ["django_snippets"]  # used in contact form and (debug) profiling middleware
TEMPLATE_CONTEXT_PROCESSORS += ["django.core.context_processors.debug"]  # used in conjunction with toolbar to show query information

#######################################
# DEBUG TOOLBAR
#######################################

INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE_CLASSES += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'fle_utils.django_utils.middleware.JsonAsHTML'
]
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'HIDE_DJANGO_SQL': False,
    'ENABLE_STACKTRACES' : True,
}
# Debug toolbar must be set in conjunction with CACHE_TIME=0
CACHE_TIME = 0
