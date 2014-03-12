import getpass
import hashlib
import json
import logging
import os
import platform
import sys
import tempfile
import time
import uuid
import version  # in danger of a circular import.  NEVER add settings stuff there--should all be hard-coded.


##############################
# Functions for querying settings
##############################

def package_selected(package_name):
    global CONFIG_PACKAGE
    return bool(CONFIG_PACKAGE) and bool(package_name) and package_name.lower() in CONFIG_PACKAGE

def user_facing_port():
    global PROXY_PORT
    global PRODUCTION_PORT
    return PROXY_PORT or PRODUCTION_PORT


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
# Basic App Settings
##############################

CENTRAL_SERVER = getattr(local_settings, "CENTRAL_SERVER", False)

# the default encoding for strings read from various IO sources
DEFAULT_ENCODING = getattr(local_settings, "DEFAULT_ENCODING", 'utf-8')

# set the default encoding
# OK, so why do we reload sys? Because apparently sys.setdefaultencoding
# is deleted somewhere at startup. Reloading brings it back.
# see: http://blog.ianbicking.org/illusive-setdefaultencoding.html
reload(sys)
sys.setdefaultencoding(DEFAULT_ENCODING)

PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 8008 if not CENTRAL_SERVER else 8001)
#proxy port is used by nginx and is used by Raspberry Pi optimizations
PROXY_PORT = getattr(local_settings, "PROXY_PORT", None)
CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 18 if not DEBUG else 5)  # 18 threads seems a sweet spot

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
CENTRAL_SERVER_HOST   = getattr(local_settings, "CENTRAL_SERVER_HOST",   ("globe.%s:8008" if DEBUG else "kalite.%s") % CENTRAL_SERVER_DOMAIN)
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s" % CENTRAL_SERVER_DOMAIN)
CENTRAL_DEPLOYMENT_EMAIL = getattr(local_settings, "CENTRAL_DEPLOYMENT_EMAIL", "deployments@learningequality.org")
CENTRAL_SUPPORT_EMAIL = getattr(local_settings, "CENTRAL_SUPPORT_EMAIL",    "support@learningequality.org")
CENTRAL_DEV_EMAIL     = getattr(local_settings, "CENTRAL_DEV_EMAIL",        "dev@learningequality.org")
CENTRAL_INFO_EMAIL    = getattr(local_settings, "CENTRAL_INFO_EMAIL",       "info@learningequality.org")
CENTRAL_CONTACT_EMAIL = getattr(local_settings, "CENTRAL_CONTACT_EMAIL", "info@%s" % CENTRAL_SERVER_DOMAIN)
CENTRAL_ADMIN_EMAIL   = getattr(local_settings, "CENTRAL_ADMIN_EMAIL",   "errors@%s" % CENTRAL_SERVER_DOMAIN)

CENTRAL_SUBSCRIBE_URL    = getattr(local_settings, "CENTRAL_SUBSCRIBE_URL",    "http://adhocsync.us6.list-manage.com/subscribe/post?u=023b9af05922dfc7f47a4fffb&amp;id=97a379de16")

PROJECT_PATH   = os.path.realpath(getattr(local_settings, "PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))) + "/"

LOCALE_PATHS   = getattr(local_settings, "LOCALE_PATHS", (PROJECT_PATH + "/../locale",))
LOCALE_PATHS   = tuple([os.path.realpath(lp) + "/" for lp in LOCALE_PATHS])

SCRIPTS_PATH   = getattr(local_settings, "SCRIPTS_PATH", os.path.join(PROJECT_PATH, '..', 'scripts'))

DATABASES      = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": getattr(local_settings, "DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME"  : getattr(local_settings, "DATABASE_PATH", os.path.join(PROJECT_PATH, "database", "data.sqlite")),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})


##############################
# Basic Django settings
##############################

INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))

ADMINS         = getattr(local_settings, "ADMINS", ( ("KA Lite Team", CENTRAL_ADMIN_EMAIL), ) )

MANAGERS       = getattr(local_settings, "MANAGERS", ADMINS)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = getattr(local_settings, "TIME_ZONE", None)
#USE_TZ         = True  # needed for timezone-aware datetimes (particularly in updates code)

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

# Other defined paths
DATA_PATH = os.path.realpath(getattr(local_settings, "DATA_PATH", os.path.join(PROJECT_PATH, "..", "data"))) + "/"

# JSON file of all languages and their names
LANG_LOOKUP_FILEPATH = os.path.join(DATA_PATH, "i18n", "languagelookup.json")

 # Make this unique, and don't share it with anybody.
SECRET_KEY     = getattr(local_settings, "SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

TEMPLATE_DIRS  = getattr(local_settings, "TEMPLATE_DIRS", (PROJECT_PATH + "/templates",))
TEMPLATE_DIRS  = tuple([os.path.realpath(td) + "/" for td in TEMPLATE_DIRS])

HTTP_PROXY     = getattr(local_settings, "HTTP_PROXY", None)
HTTPS_PROXY     = getattr(local_settings, "HTTPS_PROXY", None)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
)
if USE_I18N:
    TEMPLATE_CONTEXT_PROCESSORS += ("django.core.context_processors.i18n",)
TEMPLATE_CONTEXT_PROCESSORS += (
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
#    if USE_I18N:
TEMPLATE_CONTEXT_PROCESSORS += ("i18n.custom_context_processors.languages",)

MIDDLEWARE_CLASSES = getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "utils.django_utils.middleware.GetNextParam",
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
    "facility",
    "config",
    "main", # in order for securesync to work, this needs to be here.
    "control_panel",  # in both apps
    "coachreports",  # in both apps; reachable on central via control_panel
    "khanload",  # khan academy interactions
    "updates",  #
    "i18n",  #
    "kalite",  # contains commands
) + INSTALLED_APPS  # append local_settings installed_apps, in case of dependencies

if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware

if CENTRAL_SERVER:
    ROOT_URLCONF = "central.urls"
    ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central", "faq", "contact", "stats", "announcements",)
    EMAIL_BACKEND           = getattr(local_settings, "EMAIL_BACKEND", "postmark.backends.PostmarkBackend")
    AUTH_PROFILE_MODULE     = "central.UserProfile"
    CSRF_COOKIE_NAME        = "csrftoken_central"
    LANGUAGE_COOKIE_NAME    = "django_language_central"
    SESSION_COOKIE_NAME     = "sessionid_central"

    CROWDIN_PROJECT_ID      = getattr(local_settings, "CROWDIN_PROJECT_ID", None)
    CROWDIN_PROJECT_KEY     = getattr(local_settings, "CROWDIN_PROJECT_KEY", None)
    AMARA_USERNAME          = getattr(local_settings, "AMARA_USERNAME", None)
    AMARA_API_KEY           = getattr(local_settings, "AMARA_API_KEY", None)

    CONTENT_ROOT   = None  # needed for shared functions that are main-only
    CONTENT_URL    = None

else:
    ROOT_URLCONF = "main.urls"
    MIDDLEWARE_CLASSES += (
        "facility.middleware.AuthFlags",  # this must come first in app-dependent middleware--many others depend on it.
        "facility.middleware.FacilityCheck",
        "securesync.middleware.RegisteredCheck",
        "securesync.middleware.DBCheck",
        "kalite.i18n.middleware.SessionLanguage",
        "facility.middleware.LockdownCheck",
    )

    TEMPLATE_CONTEXT_PROCESSORS += ("i18n.custom_context_processors.languages",)
    INSTALLED_APPS += ('i18n', 'testing')
    LANGUAGE_COOKIE_NAME    = "django_language"

    CONTENT_ROOT   = os.path.realpath(getattr(local_settings, "CONTENT_ROOT", PROJECT_PATH + "/../content/")) + "/"
    CONTENT_URL    = getattr(local_settings, "CONTENT_URL", "/content/")

# Must define after i18n.middleware.SessionLanguage
MIDDLEWARE_CLASSES += (
    'django.middleware.locale.LocaleMiddleware',
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

SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https" if not DEBUG else "http")

CRONSERVER_FREQUENCY = getattr(local_settings, "CRONSERVER_FREQUENCY", 600) # 10 mins (in seconds)

SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", None)  # default: don't throttle syncing

SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 100)  # 100 records per http request


# Here, None === no limit
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", None if CENTRAL_SERVER else 10)

# Used for user logs.  By default, completely off.
#  Note: None means infinite (just like caching)
USER_LOG_MAX_RECORDS_PER_USER = getattr(local_settings, "USER_LOG_MAX_RECORDS_PER_USER", 1)
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
assert PASSWORD_ITERATIONS_STUDENT_SYNCED >= 2500, "PASSWORD_ITERATIONS_STUDENT_SYNCED must be >= 2500"

PASSWORD_CONSTRAINTS = getattr(local_settings, "PASSWORD_CONSTRAINTS", {
    'min_length': getattr(local_settings, 'PASSWORD_MIN_LENGTH', 6),
})

LOCKDOWN = getattr(local_settings, "LOCKDOWN", False)


########################
# Storage and caching
########################

# Sessions use the default cache, and we want a local memory cache for that.
# Separate session caching from file caching.
SESSION_ENGINE = getattr(local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.cache' + ('d_db' if DEBUG else ''))

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
CACHE_TIME = getattr(local_settings, "CACHE_TIME", _max_cache_time if not CENTRAL_SERVER else 0)
CACHE_NAME = getattr(local_settings, "CACHE_NAME", None)  # without a cache defined, None is fine

# Cache is activated in every case,
#   EXCEPT: if CACHE_TIME=0
if CACHE_TIME != 0:  # None can mean infinite caching to some functions
    KEY_PREFIX = version.VERSION_INFO[version.VERSION]["git_commit"][0:6]  # new cache for every build

    # File-based cache
    install_location_hash = hashlib.sha1(PROJECT_PATH).hexdigest()
    username = getpass.getuser() or "unknown_user"
    cache_dir_name = "kalite_web_cache_%s" % (username)
    CACHE_LOCATION = os.path.realpath(getattr(local_settings, "CACHE_LOCATION", os.path.join(tempfile.gettempdir(), cache_dir_name, install_location_hash))) + "/"
    CACHES["file_based_cache"] = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': CACHE_LOCATION, # this is kind of OS-specific, so dangerous.
        'TIMEOUT': CACHE_TIME, # should be consistent
        'OPTIONS': {
            'MAX_ENTRIES': getattr(local_settings, "CACHE_MAX_ENTRIES", 5*2000) #2000 entries=~10,000 files
        },
    }

    # Memory-based cache
    CACHES["mem_cache"] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': CACHE_TIME, # should be consistent
        'OPTIONS': {
            'MAX_ENTRIES': getattr(local_settings, "CACHE_MAX_ENTRIES", 5*2000) #2000 entries=~10,000 files
        },
    }

    # The chosen cache
    CACHE_NAME = getattr(local_settings, "CACHE_NAME", "file_based_cache")
    if CACHE_NAME == "file_based_cache":
        LOG.debug("Cache location = %s" % CACHE_LOCATION)
    else:
        LOG.debug("Using %s caching" % CACHE_NAME)


########################
# Features
########################


if CENTRAL_SERVER:
    # Used for accessing the KA API.
    #   By default, things won't work--local_settings needs to specify good values.
    #   We do this so that we have control over our own key/secret (secretly, of course!)
    KHAN_API_CONSUMER_KEY = getattr(local_settings, "KHAN_API_CONSUMER_KEY", "")
    KHAN_API_CONSUMER_SECRET = getattr(local_settings, "KHAN_API_CONSUMER_SECRET", "")

    # Postmark settings, to enable sending registration/invitation emails
    POSTMARK_API_KEY = getattr(local_settings, "POSTMARK_API_KEY", "")
    POSTMARK_SENDER = getattr(local_settings, "POSTMARK_SENDER", CENTRAL_FROM_EMAIL)
    # Default to "test mode" if no API key, to print out the email to the console, rather than trying to send
    POSTMARK_TEST_MODE = getattr(local_settings, "POSTMARK_TEST_MODE", POSTMARK_API_KEY == "")

    # Used for redirecting to the actual installer executables
    INSTALLER_BASE_URL = getattr(local_settings, 'INSTALLER_BASE_URL', 'http://adhoc.learningequality.org/media/installer/')

else:
    # enable this to use a background mplayer instance instead of playing the video in the browser, on loopback connections
    # TODO(jamalex): this will currently only work when caching is disabled, as the conditional logic is in the Django template
    USE_MPLAYER = getattr(local_settings, "USE_MPLAYER", False) if CACHE_TIME == 0 else False

    # Clock Setting disabled by default unless overriden.
    # Note: This will only work on Linux systems where the server is running as root.
    ENABLE_CLOCK_SET = False


# This has to be defined for main and central
# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = getattr(local_settings, "BACKUP_VIDEO_SOURCE", None)
BACKUP_THUMBNAIL_SOURCE = getattr(local_settings, "BACKUP_THUMBNAIL_SOURCE", None)
assert not BACKUP_VIDEO_SOURCE or CACHE_TIME == 0, "If BACKUP_VIDEO_SOURCE, then CACHE_TIME must be 0"


########################
# Debugging and testing
########################

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

if not CENTRAL_SERVER and os.path.exists(PROJECT_PATH + "/testing/loadtesting/"):
        INSTALLED_APPS += ("testing.loadtesting",)

TEST_RUNNER = 'kalite.testing.testrunner.KALiteTestRunner'

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["fast", "medium", "long"])), "TESTS_TO_SKIP must contain only 'fast', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)



########################
# (Aron): Setting the LANGUAGES configuration.
########################

# This is a bit more involved, as we need to hand out to a function to calculate
# the LANGUAGES settings. This LANGUAGES setting is basically a whitelist of
# languages. Anything not in here is not accepted by Django, and will simply show
# english instead of the selected language.
if getattr(local_settings, 'LANGUAGES', None):
    LANGUAGES = local_settings.LANGUAGES
else:
    from settingshelper import allow_all_languages_alist
    # copied from shared.i18n
    try:
        LANGUAGES = set(allow_all_languages_alist(LANG_LOOKUP_FILEPATH))
    except Exception:
        LOG.error("%s not found. Django will use its own builtin LANGUAGES list." % LANG_LOOKUP_FILEPATH)


########################
# IMPORTANT: Do not add new settings below this line
# everything that follows is overriding default settings, depending on CONFIG_PACKAGE

# config_package (None|RPi) alters some defaults e.g. different defaults for Raspberry Pi(RPi)
# autodetect if this is a Raspberry Pi-type device, and auto-set the config_package
#  to override the auto-detection, set CONFIG_PACKAGE=None in the local_settings

CONFIG_PACKAGE = getattr(local_settings, "CONFIG_PACKAGE",
                   ("RPi" if platform.uname()[0] == "Linux" and platform.uname()[4] == "armv6l" and not CENTRAL_SERVER
                   else []))

if isinstance(CONFIG_PACKAGE, basestring):
    CONFIG_PACKAGE = [CONFIG_PACKAGE]
CONFIG_PACKAGE = [cp.lower() for cp in CONFIG_PACKAGE]

# Config for Raspberry Pi distributed server
if package_selected("RPi"):
    logging.info("RPi package selected.")
    # nginx proxy will normally be on 8008 and production port on 7007
    # If ports are overridden in local_settings, run the optimizerpi script
    PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 7007)
    PROXY_PORT = getattr(local_settings, "PROXY_PORT", 8008)
    assert PRODUCTION_PORT != PROXY_PORT, "PRODUCTION_PORT and PROXY_PORT must not be the same"
    #SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", 1.0)
    #SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 10)

    PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", 2000)
    PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", 500)

    ENABLE_CLOCK_SET = getattr(local_settings, "ENABLE_CLOCK_SET", True)

if package_selected("UserRestricted"):
    LOG.info("UserRestricted package selected.")

    if CACHE_TIME != 0 and not hasattr(local_settings, KEY_PREFIX):
        KEY_PREFIX += "|restricted"  # this option changes templates

if package_selected("Demo"):
    LOG.info("Demo package selected.")

    CENTRAL_SERVER_HOST = getattr(local_settings, "CENTRAL_SERVER_HOST",   "globe.learningequality.org:8008")
    SECURESYNC_PROTOCOL = "http"
    DEMO_ADMIN_USERNAME = getattr(local_settings, "DEMO_ADMIN_USERNAME", "admin")
    DEMO_ADMIN_PASSWORD = getattr(local_settings, "DEMO_ADMIN_PASSWORD", "pass")

    MIDDLEWARE_CLASSES += ('main.demo_middleware.StopAdminAccess','main.demo_middleware.LinkUserManual','main.demo_middleware.ShowAdminLogin',)
