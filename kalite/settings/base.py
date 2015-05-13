import logging
import os
import json
import sys
import warnings

from kalite import ROOT_DATA_PATH
from kalite.shared.warnings import RemovedInKALite_v015_Warning


# Load local settings first... loading it again later to have the possibility
# to overwrite default app settings.. very strange method, will be refactored
# and completely fixed ~0.14 or 0.15. /benjaoming

try:
    # Not sure if vars from local_settings are accessed ATM. This is one of
    # the big disadvantage of this whole implicit importing chaos... will be
    # fixed later.
    from kalite import local_settings
    # This is not a DeprecationWarning by purpose, because those are
    # ignored during settings module load time
    warnings.warn(
        "We will be deprecating the old way of statically importing custom "
        "settings, in favor of a more flexible way. The easiest way to update "
        "your installation is to rename your local_settings.py (keeping it in "
        "the same directory) and add an import statement in the very first "
        "line of the new file so it looks like this:\n\n"
        "    from kalite.settings.base import *\n"
        "    # Put custom settings here...\n"
        "    FOO = BAR\n\n"
        "and then call kalite start with an additional argument pointing to "
        "your new settings module:\n\n"
        "    kalite start --settings=kalite.my_settings\n\n"
        "In the future, it is recommended not to keep your own settings module "
        "in the kalite code base but to put the file somewhere else in your "
        "python path, for instance in the current directory when running "
        "'kalite --settings=my_module'.",
        RemovedInKALite_v015_Warning
    )
except ImportError:
    local_settings = object()


##############################
# Basic setup
##############################

# Used everywhere, so ... set it up top.
DEBUG = getattr(local_settings, "DEBUG", False)

CENTRAL_SERVER = False  # Hopefully will be removed soon.

##############################
# Basic setup of logging
##############################

# TODO: Use Django's settings.LOGGERS

# Set logging level based on the value of DEBUG (evaluates to 0 if False,
# 1 if True)
LOGGING_LEVEL = getattr(
    local_settings, "LOGGING_LEVEL", logging.DEBUG if DEBUG else logging.INFO)
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))

TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

logging.basicConfig()
LOG.setLevel(LOGGING_LEVEL)
logging.getLogger("requests").setLevel(logging.WARNING)  # shut up requests!


##############################
# Basic Django settings
##############################

###################################################
# RUNNING FROM STATIC SOURCE DIR?
###################################################
#
# ka-lite can be run from a source directory, such
# that all data files and user data are stored in
# one static structure.
default_source_path = os.path.split(
    os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
)[0]
if not default_source_path:
    default_source_path = '.'

IS_SOURCE = (
    os.path.exists(os.path.join(default_source_path, '.KALITE_SOURCE_DIR')) and
    (
        'kalitectl.py' not in sys.argv[0] or
        os.path.realpath(sys.argv[0]) == os.path.realpath(os.path.join(default_source_path, 'kalitectl.py'))
    )
)
SOURCE_DIR = None


# Not sure if this is relevant anymore? /benjaoming
BUILD_INDICATOR_FILE = os.path.join(default_source_path, "_built.touch")
# whether this installation was processed by the build server
BUILT = os.path.exists(BUILD_INDICATOR_FILE)


if IS_SOURCE:
    # We assume that the project source is 2 dirs up from the settings/base.py file
    _data_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    SOURCE_DIR = _data_path

    if not _data_path:
        _data_path = '.'
    
    # This is getting deprecated as we will not explicitly operate with a static
    # source structure, but have shared system-wide data and user data.
    # It's not actually even a project root, because it's also the application's
    # own package root.
    default_project_root = os.path.join(
        _data_path,
        'kalite'
    )

    # BEING DEPRECATED, PLEASE DO NOT USE PROJECT_PATH!
    PROJECT_PATH = os.path.realpath(
        getattr(
            local_settings,
            "PROJECT_PATH",
            default_project_root
        )
    )
    
else:
    _data_path = os.path.join(ROOT_DATA_PATH,)
    
    # BEING DEPRECATED, PLEASE DO NOT USE PROJECT_PATH!
    PROJECT_PATH = os.environ.get(
        "KALITE_HOME",
        os.path.join(os.path.expanduser("~"), ".kalite")
    )


###################################################
# CHANNEL and CONTENT DATA
###################################################
#
# Currently, this stuff is either in a source dir installation,
# ka-lite/content
# ka-lite/locales
#
# ...OR it's been installed in:
# sys.prefix/share/kalite/content
# sys.prefix/share/kalite/locales


_data_path_channels = os.path.join(_data_path, 'data')

CHANNEL = getattr(local_settings, "CHANNEL", "khan")

CONTENT_DATA_PATH = getattr(local_settings, "CONTENT_DATA_PATH", _data_path_channels)
CHANNEL_DATA_PATH = os.path.join(CONTENT_DATA_PATH, CHANNEL)

CONTENT_DATA_URL = getattr(local_settings, "CONTENT_DATA_URL", "/data/")


# Parsing a whole JSON file just to load the settings is not nice
try:
    CHANNEL_DATA = json.load(open(os.path.join(CHANNEL_DATA_PATH, "channel_data.json"), 'r'))
except IOError:
    CHANNEL_DATA = {}

# Whether we wanna load the perseus assets. Set to False for testing for now.
LOAD_KHAN_RESOURCES = getattr(local_settings, "LOAD_KHAN_RESOURCES", CHANNEL == "khan")


###################################################
# USER DATA
###################################################
#
# This is related to data that can be modified by
# the user running kalite and should be in a user-data
# storage place.

USER_DATA_ROOT = os.environ.get(
    "KALITE_HOME",
    os.path.join(os.path.expanduser("~"), ".kalite")
)


# Most of these data locations are messed up because of legacy
if IS_SOURCE:
    USER_DATA_ROOT = SOURCE_DIR
    LOCALE_PATHS = getattr(local_settings, "LOCALE_PATHS", (os.path.join(USER_DATA_ROOT, 'locale'),))
    LOCALE_PATHS = tuple([os.path.realpath(lp) + "/" for lp in LOCALE_PATHS])
    
    # This is the legacy location kalite/database/data.sqlite
    DEFAULT_DATABASE_PATH = os.path.join(_data_path, "kalite", "database", "data.sqlite")

    MEDIA_ROOT = os.path.join(_data_path, "kalite", "media")
    STATIC_ROOT = os.path.join(_data_path, "kalite", "static")


# Storing data in a user directory
else:
    
    # Ensure that path exists
    if not os.path.exists(USER_DATA_ROOT):
        os.mkdir(USER_DATA_ROOT)
    
    LOCALE_PATHS = getattr(local_settings, "LOCALE_PATHS", (os.path.join(USER_DATA_ROOT, 'locale'),))
    for path in LOCALE_PATHS:
        if not os.path.exists(path):
            os.mkdir(path)
    
    DEFAULT_DATABASE_PATH = os.path.join(USER_DATA_ROOT, "database",)
    if not os.path.exists(DEFAULT_DATABASE_PATH):
        os.mkdir(DEFAULT_DATABASE_PATH)
    
    DEFAULT_DATABASE_PATH = os.path.join(DEFAULT_DATABASE_PATH, 'default.sqlite')
    
    # Stuff that can be served by the HTTP server is located the same place
    # for convenience and security
    HTTPSRV_PATH = os.path.join(USER_DATA_ROOT, 'httpsrv')
    if not os.path.exists(HTTPSRV_PATH):
        os.mkdir(HTTPSRV_PATH)
    MEDIA_ROOT = os.path.join(HTTPSRV_PATH, "media")
    STATIC_ROOT = os.path.join(HTTPSRV_PATH, "static")


# Necessary for Django compressor
if not DEBUG:
    STATICFILES_FINDERS = (
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "compressor.finders.CompressorFinder",
    )


# Overwrite stuff from local_settings
MEDIA_ROOT = getattr(local_settings, "MEDIA_ROOT", MEDIA_ROOT)
STATIC_ROOT = getattr(local_settings, "STATIC_ROOT", STATIC_ROOT)
MEDIA_URL = getattr(local_settings, "MEDIA_URL", "/media/")
STATIC_URL = getattr(local_settings, "STATIC_URL", "/static/")
DEFAULT_DATABASE_PATH = getattr(local_settings, "DATABASE_PATH", DEFAULT_DATABASE_PATH)

DATABASES = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": getattr(local_settings, "DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME": DEFAULT_DATABASE_PATH,
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

INTERNAL_IPS = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))
ALLOWED_HOSTS = getattr(local_settings, "ALLOWED_HOSTS", ['*'])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = getattr(local_settings, "TIME_ZONE", None)
# USE_TZ         = True  # needed for timezone-aware datetimes
# (particularly in updates code)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = getattr(local_settings, "LANGUAGE_CODE", "en")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = getattr(local_settings, "USE_I18N", True)

# If you set this to True, Django will format dates, numbers and
# calendars according to the current locale
USE_L10N = getattr(local_settings, "USE_L10N", False)

# Make this unique, and don't share it with anybody.
SECRET_KEY = getattr(local_settings, "SECRET_KEY",
                     "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

LANGUAGE_COOKIE_NAME = "django_language"

ROOT_URLCONF = "kalite.distributed.urls"

INSTALLED_APPS = (
    # this and the following are needed to enable django admin.
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "kalite.distributed",
    "compressor",
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
    # gzip has to be placed at the top, before others
    "django.middleware.gzip.GZipMiddleware",
    # needed for django admin
    "django.contrib.messages.middleware.MessageMiddleware",
    "django_snippets.session_timeout_middleware.SessionIdleTimeout",
) + getattr(local_settings, 'MIDDLEWARE_CLASSES', tuple())

TEMPLATE_CONTEXT_PROCESSORS = (
    # needed for django admin
    "django.contrib.messages.context_processors.messages",
) + getattr(local_settings, 'TEMPLATE_CONTEXT_PROCESSORS', tuple())

TEMPLATE_DIRS = tuple()  # will be filled recursively via INSTALLED_APPS
# libraries common to all apps
STATICFILES_DIRS = (os.path.join(_data_path, 'static-libraries'),)

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
SESSION_ENGINE = getattr(
    local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.cache' + (''))

# Use our custom message storage to avoid adding duplicate messages
MESSAGE_STORAGE = 'fle_utils.django_utils.classes.NoDuplicateMessagesSessionStorage'

# disable migration framework on tests
SOUTH_TESTS_MIGRATE = False

# only allow, and use by default, JSON in tastypie, and remove api page limit
TASTYPIE_DEFAULT_FORMATS = ['json']
API_LIMIT_PER_PAGE = 0

# Default to a 20 minute timeout for a session - set to 0 to disable.
# TODO(jamalex): re-enable this to something sensible, once #2800 is resolved
SESSION_IDLE_TIMEOUT = getattr(local_settings, "SESSION_IDLE_TIMEOUT", 0)


# DEPRECATED BEHAVIOURS

# Copy INSTALLED_APPS to prevent any overwriting
OLD_INSTALLED_APPS = INSTALLED_APPS[:]

# NOW OVER WRITE EVERYTHING WITH ANY POSSIBLE LOCAL SETTINGS
try:
    from kalite.local_settings import *  # @UnusedWildImport
except ImportError:
    pass

# Ensure that any INSTALLED_APPS mentioned in local_settings is concatenated
# to previous INSTALLED_APPS because that was expected behaviour in 0.13
try:
    from kalite.local_settings import INSTALLED_APPS
    INSTALLED_APPS = OLD_INSTALLED_APPS + INSTALLED_APPS
except ImportError:
    pass
