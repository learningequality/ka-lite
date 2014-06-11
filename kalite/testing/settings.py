import os

try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

# Django debug_toolbar config
INSTALLED_APPS = (
    'kalite.facility',  # Create users
    'kalite.main',  # Probing / creating Log objects, accessing topic_tools
    'kalite.main',  # Probing / creating Log objects
    'kalite.topic_tools',  # For benchmarking, finding random exercises
    'securesync',  # Uses securesync testing hooks
)
MIDDLEWARE_CLASSES = tuple()


#######################
# Set module settings
#######################

USE_DEBUG_TOOLBAR = getattr(local_settings, "USE_DEBUG_TOOLBAR", False)

if USE_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
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

if getattr(local_settings, "DEBUG", False):
    INSTALLED_APPS += (
        "django.contrib.admin",  # this and the following are needed to enable django admin.
    )

    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += (
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        'django_snippets.profiling_middleware.ProfileMiddleware',
    )

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
    )



if os.path.exists(os.path.join(os.path.dirname(__file__), "loadtesting")):
    INSTALLED_APPS += (__package__ + ".loadtesting",)

KALITE_TEST_RUNNER = __package__ + ".testrunner.KALiteTestRunner"

RUNNING_IN_TRAVIS = bool(os.environ.get("TRAVIS"))

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["medium", "long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["short", "medium", "long"])), "TESTS_TO_SKIP must contain only 'short', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)


