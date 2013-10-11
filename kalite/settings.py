import json
import logging
import os
import sys
import tempfile
import time
import uuid
import version  # in danger of a circular import.  NEVER add settings stuff there--should all be hard-coded.

##############################
# Basic setup (no options)
##############################

# suppress warnings here.
try:
    import warnings
    warnings.simplefilter("ignore") # any other filter was ineffecual or threw an error
except:
    pass

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

# Add additional mimetypes to avoid errors/warnings
import mimetypes
mimetypes.add_type("font/opentype", ".otf", True)


# Used everywhere, so ... set it up top.
DEBUG          = getattr(local_settings, "DEBUG", False)


##############################
# Basic App Settings 
##############################

CENTRAL_SERVER = getattr(local_settings, "CENTRAL_SERVER", False)

PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 8008 if not CENTRAL_SERVER else 8001)
CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 50 if not DEBUG else 5)

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "adhocsync.com")
CENTRAL_SERVER_HOST   = getattr(local_settings, "CENTRAL_SERVER_HOST",   "kalite.%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.learningequality.org/")#http://%kalitewiki.s/%CENTRAL_SERVER_DOMAIN
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_DEPLOYMENT_EMAIL = getattr(local_settings, "CENTRAL_DEPLOYMENT_EMAIL", "deployments@learningequality.org")
CENTRAL_SUPPORT_EMAIL = getattr(local_settings, "CENTRAL_SUPPORT_EMAIL",    "support@learningequality.org")
CENTRAL_DEV_EMAIL     = getattr(local_settings, "CENTRAL_DEV_EMAIL",        "dev@learningequality.org")
CENTRAL_INFO_EMAIL    = getattr(local_settings, "CENTRAL_INFO_EMAIL",       "info@learningequality.org")
CENTRAL_CONTACT_EMAIL = getattr(local_settings, "CENTRAL_CONTACT_EMAIL", "info@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN
CENTRAL_ADMIN_EMAIL   = getattr(local_settings, "CENTRAL_ADMIN_EMAIL",   "errors@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN

CENTRAL_SUBSCRIBE_URL    = getattr(local_settings, "CENTRAL_SUBSCRIBE_URL",    "http://adhocsync.us6.list-manage.com/subscribe/post?u=023b9af05922dfc7f47a4fffb&amp;id=97a379de16")

PROJECT_PATH   = os.path.realpath(getattr(local_settings, "PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))) + "/"

LOCALE_PATHS   = getattr(local_settings, "LOCALE_PATHS", (PROJECT_PATH + "/../locale",))
LOCALE_PATHS   = tuple([os.path.realpath(lp) + "/" for lp in LOCALE_PATHS])

DATABASES      = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": getattr(local_settings, "DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME"  : getattr(local_settings, "DATABASE_PATH", PROJECT_PATH + "/database/data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

DATA_PATH      = os.path.realpath(getattr(local_settings, "DATA_PATH", PROJECT_PATH + "/static/data/")) + "/"

SUBTITLES_DATA_ROOT = os.path.realpath(getattr(local_settings, "SUBTITLES_DATA_ROOT", DATA_PATH + "subtitles/")) + "/"

CONTENT_ROOT   = os.path.realpath(getattr(local_settings, "CONTENT_ROOT", PROJECT_PATH + "/../content/")) + "/"
CONTENT_URL    = getattr(local_settings, "CONTENT_URL", "/content/")


##############################
# Basic Django settings 
##############################

INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))

ADMINS         = getattr(local_settings, "ADMINS", ( ("KA Lite Team", CENTRAL_ADMIN_EMAIL), ) )

MANAGERS       = getattr(local_settings, "MANAGERS", ADMINS)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = getattr(local_settings, "TIME_ZONE", "America/Los_Angeles")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = getattr(local_settings, "LANGUAGE_CODE", "en-us")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = getattr(local_settings, "USE_I18N", True)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N       = getattr(local_settings, "USE_L10N", False)

MEDIA_URL      = getattr(local_settings, "MEDIA_URL", "/media/")
MEDIA_ROOT     = os.path.realpath(getattr(local_settings, "MEDIA_ROOT", PROJECT_PATH + "/media/")) + "/"
STATIC_URL     = getattr(local_settings, "STATIC_URL", "/static/")
STATIC_ROOT    = os.path.realpath(getattr(local_settings, "STATIC_ROOT", PROJECT_PATH + "/static/")) + "/"

 # Make this unique, and don't share it with anybody.
SECRET_KEY     = getattr(local_settings, "SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

TEMPLATE_DIRS  = getattr(local_settings, "TEMPLATE_DIRS", (PROJECT_PATH + "/templates",))
TEMPLATE_DIRS  = tuple([os.path.realpath(td) + "/" for td in TEMPLATE_DIRS])

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "%s.custom_context_processors.custom" % ("central" if CENTRAL_SERVER else "main"),
)


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
#     "django.template.loaders.eggs.Loader",
)

MIDDLEWARE_CLASSES = getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.GetNextParam",
    "django.middleware.csrf.CsrfViewMiddleware",
) + MIDDLEWARE_CLASSES  # append local_settings middleware, in case of dependencies

INSTALLED_APPS = getattr(local_settings, 'INSTALLED_APPS', tuple())
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions", # needed for clean_pyc (testing)
    "south",
    "chronograph",
    "django_cherrypy_wsgiserver",
    "securesync",
    "config",
    "main", # in order for securesync to work, this needs to be here.
    "control_panel",  # in both apps
    "coachreports",  # in both apps; reachable on central via control_panel
    "khanload",  # khan academy interactions
    "i18n",
    "kalite",  # contains commands
) + INSTALLED_APPS  # append local_settings installed_apps, in case of dependencies


if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware

if CENTRAL_SERVER:
    ROOT_URLCONF = "central.urls"
    ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central", "faq", "contact", "stats")
    EMAIL_BACKEND           = getattr(local_settings, "EMAIL_BACKEND", "postmark.backends.PostmarkBackend")
    AUTH_PROFILE_MODULE     = "central.UserProfile"
    CSRF_COOKIE_NAME        = "csrftoken_central"
    LANGUAGE_COOKIE_NAME    = "django_language_central"
    SESSION_COOKIE_NAME     = "sessionid_central"

else:
    ROOT_URLCONF = "main.urls"
    INSTALLED_APPS += ("updates",)
    MIDDLEWARE_CLASSES += (
        "securesync.middleware.AuthFlags",  # this must come first in app-dependent middleware--many others depend on it.
        "securesync.middleware.FacilityCheck",
        "securesync.middleware.RegisteredCheck",
        "securesync.middleware.DBCheck",
        "main.middleware.SessionLanguage",
    )


########################
# Zero-config options
########################

ZERO_CONFIG   = getattr(local_settings, "ZERO_CONFIG", False)

# With zero config, no admin (by default)
INSTALL_ADMIN_USERNAME = getattr(local_settings, "INSTALL_ADMIN_USERNAME", None)
INSTALL_ADMIN_PASSWORD = getattr(local_settings, "INSTALL_ADMIN_PASSWORD", None)
assert bool(INSTALL_ADMIN_USERNAME) + bool(INSTALL_ADMIN_PASSWORD) != 1, "Must specify both admin username and password, or neither."

# With zero config, always a default facility
INSTALL_FACILITY_NAME = getattr(local_settings, "INSTALL_FACILITY_NAME", None if not ZERO_CONFIG else "Default Facility")


########################
# Syncing and synced data
########################

SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https")

CRONSERVER_FREQUENCY = getattr(local_settings, "CRONSERVER_FREQUENCY", 600) # 10 mins (in seconds)

SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", None)  # default: don't throttle syncing

SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 100)  # 100 records per http request


# Here, None === no limit
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", None if CENTRAL_SERVER else 10)

# Used for user logs.  By default, completely off.
#  Note: None means infinite (just like caching)
USER_LOG_MAX_RECORDS_PER_USER = getattr(local_settings, "USER_LOG_MAX_RECORDS_PER_USER", 0)
USER_LOG_SUMMARY_FREQUENCY = getattr(local_settings, "USER_LOG_SUMMARY_FREQUENCY", (1,"months"))


########################
# Security
########################

# None means, use full hashing locally--turn off the password cache
PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", None)
PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", None)
assert PASSWORD_ITERATIONS_TEACHER is None or PASSWORD_ITERATIONS_TEACHER >= 1, "If set, PASSWORD_ITERATIONS_TEACHER must be >= 1"
assert PASSWORD_ITERATIONS_STUDENT is None or PASSWORD_ITERATIONS_STUDENT >= 1, "If set, PASSWORD_ITERATIONS_STUDENT must be >= 1"

# This should not be set, except in cases where additional security is desired.
PASSWORD_ITERATIONS_TEACHER_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER_SYNCED", 5000)
PASSWORD_ITERATIONS_STUDENT_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT_SYNCED", 2500)
assert PASSWORD_ITERATIONS_TEACHER_SYNCED >= 5000, "PASSWORD_ITERATIONS_TEACHER_SYNCED must be >= 5000"
assert PASSWORD_ITERATIONS_STUDENT_SYNCED >= 2500, "PASSWORD_ITERATIONS_STUDENT_SYNCED must be >= 5000"


########################
# Storage and caching
########################

# Sessions use the default cache, and we want a local memory cache for that.
# Separate session caching from file caching.
SESSION_ENGINE = getattr(local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.cached_db')

MESSAGE_STORAGE = 'utils.django_utils.NoDuplicateMessagesSessionStorage'

CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Local memory cache is to expensive to use for the page cache.
#   instead, use a file-based cache.
# By default, cache for maximum possible time.
#   Note: caching for 100 years can be too large a value
#   sys.maxint also can be too large (causes ValueError), since it's added to the current time.
#   Caching for the lesser of (100 years) or (5 years less than the max int) should work.
_5_years = 5 * 365 * 24 * 60 * 60
_100_years = 100 * 365 * 24 * 60 * 60
_max_cache_time = min(_100_years, sys.maxint - time.time() - _5_years)
CACHE_TIME = getattr(local_settings, "CACHE_TIME", _max_cache_time)

# Cache is activated in every case,
#   EXCEPT: if CACHE_TIME=0
if CACHE_TIME != 0:  # None can mean infinite caching to some functions
    CACHES["web_cache"] = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': getattr(local_settings, "CACHE_LOCATION", os.path.join(tempfile.gettempdir(), "kalite_web_cache/")), # this is kind of OS-specific, so dangerous.
        'TIMEOUT': CACHE_TIME, # should be consistent
        'OPTIONS': {
            'MAX_ENTRIES': getattr(local_settings, "CACHE_MAX_ENTRIES", 5*2000) #2000 entries=~10,000 files
        },
    }
    KEY_PREFIX = version.VERSION


########################
# Features
########################


if CENTRAL_SERVER:
    # Used for accessing the KA API.
    #   By default, things won't work--local_settings needs to specify good values.
    #   We do this so that we have control over our own key/secret (secretly, of course!)
    KHAN_API_CONSUMER_KEY = getattr(local_settings, "KHAN_API_CONSUMER_KEY", "")
    KHAN_API_CONSUMER_SECRET = getattr(local_settings, "KHAN_API_CONSUMER_SECRET", "")

else:
    # enable this to use a background mplayer instance instead of playing the video in the browser, on loopback connections
    # TODO(jamalex): this will currently only work when caching is disabled, as the conditional logic is in the Django template
    USE_MPLAYER = getattr(local_settings, "USE_MPLAYER", False) if CACHE_TIME == 0 else False

# This has to be defined for main and central

# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = getattr(local_settings, "BACKUP_VIDEO_SOURCE", None)
BACKUP_THUMBNAIL_SOURCE = getattr(local_settings, "BACKUP_THUMBNAIL_SOURCE", None)
assert not BACKUP_VIDEO_SOURCE or CACHE_TIME == 0, "If BACKUP_VIDEO_SOURCE, then CACHE_TIME must be 0"


########################
# Debugging and testing
########################

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
logging.basicConfig()
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))
LOG.setLevel(logging.DEBUG*DEBUG + logging.INFO*(1-DEBUG))

TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

# Django debug_toolbar config
if getattr(local_settings, "USE_DEBUG_TOOLBAR", False):
    assert CACHE_TIME == 0, "Debug toolbar must be set in conjunction with CACHE_TIME=0"
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

if DEBUG:
    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += ('django_snippets.profiling_middleware.ProfileMiddleware',)

if not CENTRAL_SERVER and os.path.exists(PROJECT_PATH + "/tests/loadtesting/"):
        INSTALLED_APPS += ("tests.loadtesting",)

TEST_RUNNER = 'kalite.shared.testing.testrunner.KALiteTestRunner'

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["fast", "medium", "long"])), "TESTS_TO_SKIP must contain only 'fast', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)
assert not AUTO_LOAD_TEST or not CENTRAL_SERVER, "AUTO_LOAD_TEST only on local server"


########################
# IMPORTANT: Do not add new settings below this line
# everything that follows is overriding default settings, depending on CONFIG_PACKAGE

# config_package (None|RPi) alters some defaults e.g. different defaults for Raspberry Pi(RPi)
CONFIG_PACKAGE = getattr(local_settings, "CONFIG_PACKAGE", None)

# Config for Raspberry Pi distributed server
#     nginx will normally be on 8008 so default to 7007
#     18 is the sweet-spot for cherrypy threads
#    /tmp is deleted on boot, so use /var/tmp for a persistent cache instead
if CONFIG_PACKAGE == "RPi":
    PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 7007)
    CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 18)
    #SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", 1.0)
    #SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 10)


    PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", 2000)
    PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", 1000)
    if CACHE_TIME != 0:
        CACHES["web_cache"]['LOCATION'] = getattr(local_settings, "CACHE_LOCATION", '/var/tmp/kalite_web_cache')
