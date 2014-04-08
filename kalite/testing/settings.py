import os

try:
    import local_settings
except ImportError:
    local_settings = object()


# Django debug_toolbar config
INSTALLED_APPS = tuple()
MIDDLEWARE_CLASSES = tuple()

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
    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += ('django_snippets.profiling_middleware.ProfileMiddleware',)



if os.path.exists(os.path.join(os.path.dirname(__file__), "loadtesting")):
    INSTALLED_APPS += (__package__ + ".loadtesting",)

TEST_RUNNER = __package__ + ".testrunner.KALiteTestRunner"

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["fast", "medium", "long"])), "TESTS_TO_SKIP must contain only 'fast', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)


