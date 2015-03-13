import logging
import os
import platform
from fle_utils.settingshelper import import_installed_app_settings


##############################
# Functions for querying settings
##############################

def package_selected(package_name):
    global CONFIG_PACKAGE
    return bool(CONFIG_PACKAGE) and bool(package_name) and package_name.lower() in CONFIG_PACKAGE


##############################
# Basic setup
##############################
try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = object()


# Used everywhere, so ... set it up top.
DEBUG          = getattr(local_settings, "DEBUG", False)

CENTRAL_SERVER = False  # Hopefully will be removed soon.

##############################
# Basic setup of logging
##############################

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
LOGGING_LEVEL = getattr(local_settings, "LOGGING_LEVEL", logging.DEBUG if DEBUG else logging.INFO)
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))
TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

logging.basicConfig()
LOG.setLevel(LOGGING_LEVEL)
logging.getLogger("requests").setLevel(logging.WARNING)  # shut up requests!


##############################
# Basic Django settings
##############################

# Not really a Django setting, but we treat it like one--it's eeeeverywhere.
PROJECT_PATH = os.path.realpath(getattr(local_settings, "PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))) + "/"

BUILD_INDICATOR_FILE = os.path.join(PROJECT_PATH, "_built.touch")
BUILT = os.path.exists(BUILD_INDICATOR_FILE)  # whether this installation was processed by the build server

LOCALE_PATHS   = getattr(local_settings, "LOCALE_PATHS", (PROJECT_PATH + "/../locale",))
LOCALE_PATHS   = tuple([os.path.realpath(lp) + "/" for lp in LOCALE_PATHS])

DATABASES      = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": getattr(local_settings, "DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME"  : getattr(local_settings, "DATABASE_PATH", os.path.join(PROJECT_PATH, "database", "data.sqlite")),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))
ALLOWED_HOSTS = getattr(local_settings, "ALLOWED_HOSTS", ['*'])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = getattr(local_settings, "TIME_ZONE", None)
# USE_TZ         = True  # needed for timezone-aware datetimes (particularly in updates code)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = getattr(local_settings, "LANGUAGE_CODE", "en")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = getattr(local_settings, "USE_I18N", True)

# If you set this to True, Django will format dates, numbers and
# calendars according to the current locale
USE_L10N       = getattr(local_settings, "USE_L10N", False)

MEDIA_URL      = getattr(local_settings, "MEDIA_URL", "/media/")
MEDIA_ROOT     = os.path.realpath(getattr(local_settings, "MEDIA_ROOT", PROJECT_PATH + "/media/")) + "/"
STATIC_URL     = getattr(local_settings, "STATIC_URL", "/static/")
STATIC_ROOT    = os.path.realpath(getattr(local_settings, "STATIC_ROOT", PROJECT_PATH + "/static/")) + "/"

 # Make this unique, and don't share it with anybody.
SECRET_KEY     = getattr(local_settings, "SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

LANGUAGE_COOKIE_NAME    = "django_language"

ROOT_URLCONF = "kalite.distributed.urls"

INSTALLED_APPS = (
    "django.contrib.admin",  # this and the following are needed to enable django admin.
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django_extensions", # needed for clean_pyc (testing)
    "kalite.distributed",
)

if not BUILT:
    INSTALLED_APPS += (
        "fle_utils.testing",
        "kalite.testing",
        "kalite.basetests",
    ) + getattr(local_settings, 'INSTALLED_APPS', tuple())
else:
    INSTALLED_APPS += getattr(local_settings, 'INSTALLED_APPS', tuple())

MIDDLEWARE_CLASSES = (
    "django.contrib.messages.middleware.MessageMiddleware",  # needed for django admin
    "django_snippets.session_timeout_middleware.SessionIdleTimeout",
) + getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.messages.context_processors.messages",  # needed for django admin
) + getattr(local_settings, 'TEMPLATE_CONTEXT_PROCESSORS', tuple())

TEMPLATE_DIRS  = tuple()  # will be filled recursively via INSTALLED_APPS
STATICFILES_DIRS = (os.path.join(PROJECT_PATH, '..', 'static-libraries'),)  # libraries common to all apps

DEFAULT_ENCODING = 'utf-8'

########################
# Storage and caching
########################

# Sessions use the default cache, and we want a local memory cache for that.
CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Separate session caching from file caching.
SESSION_ENGINE = getattr(local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.cache' + (''))

# Use our custom message storage to avoid adding duplicate messages
MESSAGE_STORAGE = 'fle_utils.django_utils.NoDuplicateMessagesSessionStorage'

# disable migration framework on tests
SOUTH_TESTS_MIGRATE = False

# only allow, and use by default, JSON in tastypie, and remove api page limit
TASTYPIE_DEFAULT_FORMATS = ['json']
API_LIMIT_PER_PAGE = 0

# Default to a 20 minute timeout for a session - set to 0 to disable.
# TODO(jamalex): re-enable this to something sensible, once #2800 is resolved
SESSION_IDLE_TIMEOUT = getattr(local_settings, "SESSION_IDLE_TIMEOUT", 0)

########################
# After all settings, but before config packages,
#   import settings from other apps.
#
# This allows app-specific settings to be localized and augment
#   the settings here, while also allowing
#   config packages to override settings.
########################

import_installed_app_settings(INSTALLED_APPS, globals())

# Override
CHERRYPY_PORT = getattr(local_settings, "CHERRYPY_PORT", PRODUCTION_PORT)
TEST_RUNNER = KALITE_TEST_RUNNER

########################
# IMPORTANT: Do not add new settings below this line
#
# Everything that follows is overriding default settings, depending on CONFIG_PACKAGE

# config_package (None|RPi) alters some defaults e.g. different defaults for Raspberry Pi(RPi)
# autodetect if this is a Raspberry Pi-type device, and auto-set the config_package
#  to override the auto-detection, set CONFIG_PACKAGE=None in the local_settings
########################

CONFIG_PACKAGE = getattr(local_settings, "CONFIG_PACKAGE", "RPi" if (platform.uname()[0] == "Linux" and platform.uname()[4] == "armv6l") else [])

if isinstance(CONFIG_PACKAGE, basestring):
    CONFIG_PACKAGE = [CONFIG_PACKAGE]
CONFIG_PACKAGE = [cp.lower() for cp in CONFIG_PACKAGE]


# Config for Raspberry Pi distributed server
if package_selected("RPi"):
    LOG.info("RPi package selected.")
    # nginx proxy will normally be on 8008 and production port on 7007
    # If ports are overridden in local_settings, run the optimizerpi script
    PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 7007)
    PROXY_PORT = getattr(local_settings, "PROXY_PORT", 8008)
    assert PRODUCTION_PORT != PROXY_PORT, "PRODUCTION_PORT and PROXY_PORT must not be the same"
    CHERRYPY_PORT = PRODUCTION_PORT  # re-do above override AGAIN.
    #SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", 1.0)
    #SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 10)

    PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", 2000)
    PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", 500)

    ENABLE_CLOCK_SET = getattr(local_settings, "ENABLE_CLOCK_SET", True)

    DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = True


if package_selected("nalanda"):
    LOG.info("Nalanda package selected")
    TURN_OFF_MOTIVATIONAL_FEATURES = True
    RESTRICTED_TEACHER_PERMISSIONS = True
    FIXED_BLOCK_EXERCISES = 5
    QUIZ_REPEATS = 3
UNIT_POINTS = 2000

# for extracting assessment item resources
ASSESSMENT_ITEMS_RESOURCES_DIR = os.path.join(PROJECT_PATH, "..", "content", "khan")


if package_selected("UserRestricted"):
    LOG.info("UserRestricted package selected.")

    if CACHE_TIME != 0 and not hasattr(local_settings, KEY_PREFIX):
        KEY_PREFIX += "|restricted"  # this option changes templates
    DISABLE_SELF_ADMIN = True  # hard-code facility app setting.

if package_selected("Demo"):
    LOG.info("Demo package selected.")

    CENTRAL_SERVER_HOST = getattr(local_settings, "CENTRAL_SERVER_HOST", "staging.learningequality.org")
    SECURESYNC_PROTOCOL = getattr(local_settings, "SECURESYNC_PROTOCOL", "http")
    DEMO_ADMIN_USERNAME = getattr(local_settings, "DEMO_ADMIN_USERNAME", "admin")
    DEMO_ADMIN_PASSWORD = getattr(local_settings, "DEMO_ADMIN_PASSWORD", "pass")

    MIDDLEWARE_CLASSES += ('distributed.demo_middleware.StopAdminAccess','distributed.demo_middleware.LinkUserManual','distributed.demo_middleware.ShowAdminLogin',)

if DEBUG:
    """Show DeprecationWarning messages when in debug"""
    import warnings
    warnings.simplefilter('always', DeprecationWarning)
