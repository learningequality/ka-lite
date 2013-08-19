import json
import os
import logging
import sys
import time
import tempfile

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

DEBUG          = getattr(local_settings, "DEBUG", False)
TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
logging.basicConfig()
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))
LOG.setLevel(logging.DEBUG*DEBUG + logging.INFO*(1-DEBUG))

INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))

CENTRAL_SERVER = getattr(local_settings, "CENTRAL_SERVER", False)

# TODO(jamalex): currently this only has an effect on Linux/OSX
PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 8008 if not CENTRAL_SERVER else 8001)

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)
assert not AUTO_LOAD_TEST or not CENTRAL_SERVER, "AUTO_LOAD_TEST only on local server"

# info about the central server(s)
SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https")
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

ADMINS         = getattr(local_settings, "ADMINS", ( ("KA Lite Team", CENTRAL_ADMIN_EMAIL), ) )

MANAGERS       = getattr(local_settings, "MANAGERS", ADMINS)

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

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.GetNextParam",
    "django.middleware.csrf.CsrfViewMiddleware",
)

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
    "control_panel", # in both apps
    "coachreports", # in both apps; reachable on central via control_panel
    "kalite", # contains commands
)
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware

if DEBUG:
    # add ?prof to URL, to see performance stats
    MIDDLEWARE_CLASSES += ('django_snippets.profiling_middleware.ProfileMiddleware',)

if CENTRAL_SERVER:
    ROOT_URLCONF = "central.urls"
    ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central", "faq", "contact",)
    EMAIL_BACKEND           = getattr(local_settings, "EMAIL_BACKEND", "postmark.backends.PostmarkBackend")
    AUTH_PROFILE_MODULE     = 'central.UserProfile'

else:
    ROOT_URLCONF = "main.urls"
    # Include optionally installed apps
    if os.path.exists(PROJECT_PATH + "/tests/loadtesting/"):
        INSTALLED_APPS += ("kalite.tests.loadtesting",)

    MIDDLEWARE_CLASSES += (
        "securesync.middleware.DBCheck",
        "securesync.middleware.AuthFlags",
        "main.middleware.SessionLanguage",
    )
    TEMPLATE_CONTEXT_PROCESSORS += ("main.custom_context_processors.languages",)

# Used for user logs.  By default, completely off.
USER_LOG_MAX_RECORDS = getattr(local_settings, "USER_LOG_MAX_RECORDS", 0)
USER_LOG_SUMMARY_FREQUENCY = getattr(local_settings, "USER_LOG_SUMMARY_FREQUENCY", (1,"months"))


# Sessions use the default cache, and we want a local memory cache for that.
# Separate session caching from file caching.
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
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

# Here, None === no limit
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", None if CENTRAL_SERVER else 10)

MESSAGE_STORAGE = 'utils.django_utils.NoDuplicateMessagesSessionStorage'

TEST_RUNNER = 'kalite.utils.testing.testrunner.KALiteTestRunner'

CRONSERVER_FREQUENCY = getattr(local_settings, "CRONSERVER_FREQUENCY", 600) # 10 mins (in seconds)

# Add additional mimetypes to avoid errors/warnings
import mimetypes
mimetypes.add_type("font/opentype", ".otf", True)
