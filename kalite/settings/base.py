# -*- coding: utf-8 -*-
import time
from kalite import version
import logging
import os
import sys
import warnings

from kalite import ROOT_DATA_PATH, PACKAGE_PATH
from kalite.shared.exceptions import RemovedInKALite_v016_Error

from django.utils.translation import ugettext_lazy

try:
    from kalite import local_settings
    raise RemovedInKALite_v016_Error(
        "The local_settings.py method for using custom settings has been removed."
        "In order to use custom settings, please add them to the special 'settings.py'"
        "file found in the '.kalite' subdirectory in your home directory."
    )
except ImportError:
    local_settings = object()


##############################
# Basic setup
##############################

# Used everywhere, so ... set it up top.
DEBUG = getattr(local_settings, "DEBUG", False)
TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

if DEBUG:
    warnings.warn("Setting DEBUG=True in local_settings is no longer properly supported and will not yield a true develop environment, please use --settings=kalite.project.settings.dev")


##############################
# Basic setup of logging
##############################

# Set logging level based on the value of DEBUG (evaluates to 0 if False,
# 1 if True)
LOGGING_LEVEL = getattr(local_settings, "LOGGING_LEVEL", logging.INFO)

# We should use local module level logging.getLogger
LOG = getattr(local_settings, "LOG", logging.getLogger("kalite"))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'standard': {
            'format': '[%(levelname)s] [%(asctime)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'kalite': {
            'handlers': ['console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'cherrypy.console': {
            'handlers': ['console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'cherrypy.access': {
            'handlers': ['console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'cherrypy.error': {
            'handlers': ['console'],
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# Disable the logging output on Windows, as it's broken, and was causing problems.
# See: https://github.com/learningequality/ka-lite/issues/5030
# TODO(jamalex): if we can get logging working properly on Windows, this can be removed
if os.name == "nt":
    LOGGING["handlers"]["console"]["class"] = "django.utils.log.NullHandler"


DB_TEMPLATE_DIR = os.path.join(
    os.path.split(os.path.dirname(os.path.realpath(__file__)))[0],
    "database",
    "templates"
)

DB_CONTENT_ITEM_TEMPLATE_DIR = os.path.join(
    DB_TEMPLATE_DIR,
    "content_items",
)

# DB_TEMPLATE_DEFAULT SHOULD POINT TO A PRE-GENERATED DATABASE WITH NO ROWS.
# IF IT EXISTS AND DATABASES["DEFAULT"]["NAME"] FILE DOES NOT, THEN THE LATTER WILL BE COPIED FROM THE FORMER
# IN THE SETUP MGMT COMMAND.
DB_TEMPLATE_DEFAULT = os.path.join(DB_TEMPLATE_DIR, "data.sqlite")


_data_path = ROOT_DATA_PATH

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
#
# It's NOT user-writable -- requires privileges, so any writing must be done at install time.


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

# Ensure that path exists
if not os.path.exists(USER_DATA_ROOT):
    os.mkdir(USER_DATA_ROOT)

USER_WRITABLE_LOCALE_DIR = os.path.join(USER_DATA_ROOT, 'locale')
KALITE_APP_LOCALE_DIR = os.path.join(USER_DATA_ROOT, 'locale')

LOCALE_PATHS = getattr(local_settings, "LOCALE_PATHS", (USER_WRITABLE_LOCALE_DIR, KALITE_APP_LOCALE_DIR))
if not os.path.exists(USER_WRITABLE_LOCALE_DIR):
    os.mkdir(USER_WRITABLE_LOCALE_DIR)

DEFAULT_DATABASE_DIR = os.path.join(USER_DATA_ROOT, "database",)
if not os.path.exists(DEFAULT_DATABASE_DIR):
    os.mkdir(DEFAULT_DATABASE_DIR)

DEFAULT_DATABASE_PATH = os.path.join(DEFAULT_DATABASE_DIR, 'data.sqlite')

# Stuff that can be served by the HTTP server is located the same place
# for convenience and security
HTTPSRV_PATH = os.path.join(USER_DATA_ROOT, 'httpsrv')
if not os.path.exists(HTTPSRV_PATH):
    os.mkdir(HTTPSRV_PATH)
MEDIA_ROOT = os.path.join(HTTPSRV_PATH, "media")
STATIC_ROOT = os.path.join(HTTPSRV_PATH, "static")


#######################################
# USER WRITABLE CONTENT
#######################################
# The CONTENT_ROOT is served like MEDIA_ROOT and STATIC_ROOT. Other settings
# are derived from it, see contentload.settings
#
# One of the objectives on the CONTENT_ROOT is to have an environment where data
# is copied to from online sources. For instance, the CONTENT_ROOT does NOT
# include a user's database, but it includes a lot of videos and a read-only
# database with assessment items.

# Content path-related settings
CONTENT_ROOT = os.path.realpath(os.getenv('KALITE_CONTENT_ROOT', getattr(local_settings, "CONTENT_ROOT", os.path.join(USER_DATA_ROOT, 'content'))))
if not os.path.exists(CONTENT_ROOT):
    os.makedirs(CONTENT_ROOT)
CONTENT_URL = getattr(local_settings, "CONTENT_URL", "/content/")


# Overwrite stuff from local_settings
MEDIA_ROOT = getattr(local_settings, "MEDIA_ROOT", MEDIA_ROOT)
STATIC_ROOT = getattr(local_settings, "STATIC_ROOT", STATIC_ROOT)
MEDIA_URL = getattr(local_settings, "MEDIA_URL", "/media/")
STATIC_URL = getattr(local_settings, "STATIC_URL", "/static/")


# Context data included by ka lite's context processor
KALITE_CHANNEL_CONTEXT_DATA = {
    "channel_name": ugettext_lazy(u"KA Lite"),
    "head_line": ugettext_lazy(u"A free world-class education for anyone anywhere."),
    "tag_line": ugettext_lazy(u"KA Lite is a light-weight web server for viewing and interacting with core Khan Academy content (videos and exercises) without needing an Internet connection."),
    "channel_license": u"CC-BY-NC-SA",
    "footer_text": ugettext_lazy(u"Videos © {year:d} Khan Academy (Creative Commons) // Exercises © {year:d} Khan Academy"),
    "header_logo": os.path.join(STATIC_URL, 'images', 'horizontal-logo-small.png'),
    "frontpage_splash": os.path.join(STATIC_URL, 'images', 'logo_10_enlarged_2.png'),
}


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
SECRET_KEY_FILE = getattr(
    local_settings,
    "SECRET_KEY_FILE",
    os.path.join(USER_DATA_ROOT, "secretkey.txt")
)
try:
    with open(SECRET_KEY_FILE) as f:
        SECRET_KEY = getattr(local_settings, "SECRET_KEY", f.read())
except IOError:
    sys.stderr.write("Generating a new secret key file {}...\n\n".format(SECRET_KEY_FILE))

    from ._utils import generate_secret_key, cache_secret_key
    SECRET_KEY = generate_secret_key()
    cache_secret_key(SECRET_KEY, SECRET_KEY_FILE)


LANGUAGE_COOKIE_NAME = "django_language"

ROOT_URLCONF = "kalite.distributed.urls"

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'tastypie',
    'django_js_reverse',
    'securesync',
    'south',
    'fle_utils.django_utils',
    'fle_utils.config',
    'fle_utils.chronograph',
    'kalite.coachreports',
    'kalite.distributed',
    'kalite.main',
    'kalite.updates',
    'kalite.facility',
    'kalite.student_testing',
    'kalite.topic_tools',
    'kalite.contentload',
    'kalite.dynamic_assets',
    'kalite.inline',
    'kalite.i18n',
    'kalite.control_panel',
]

INSTALLED_APPS += getattr(local_settings, 'INSTALLED_APPS', tuple())

MIDDLEWARE_CLASSES = [
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'kalite.i18n.middleware.SessionLanguage',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'fle_utils.django_utils.middleware.GetNextParam',
    'kalite.facility.middleware.AuthFlags',
    'kalite.facility.middleware.FacilityCheck',
    'securesync.middleware.RegisteredCheck',
    'securesync.middleware.DBCheck',
    'django.middleware.common.CommonMiddleware',
    'kalite.distributed.middleware.LockdownCheck',
    'kalite.distributed.middleware.LogRequests',
    'django.middleware.gzip.GZipMiddleware',
    'kalite.distributed.middleware.SessionIdleTimeout'
] + getattr(local_settings, 'MIDDLEWARE_CLASSES', [])

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.core.context_processors.i18n',
    'kalite.i18n.custom_context_processors.languages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'kalite.distributed.custom_context_processors.custom',
    'django.contrib.messages.context_processors.messages',
] + getattr(local_settings, 'TEMPLATE_CONTEXT_PROCESSORS', [])


TEMPLATE_DIRS = tuple()  # will be filled recursively via INSTALLED_APPS

# This directory is intended for the user to put their own static files in,
# for instance if they download subtitle files.
USER_STATIC_FILES = os.path.join(USER_DATA_ROOT, "static-updates")
if not os.path.exists(USER_STATIC_FILES):
    os.mkdir(USER_STATIC_FILES)

# libraries common to all apps
STATICFILES_DIRS = (
    os.path.join(PACKAGE_PATH, 'static-libraries'),
    USER_STATIC_FILES,
)

DEFAULT_ENCODING = 'utf-8'

# Due to a newer version of slimit being installed, allowing this causes an error:
# https://github.com/ierror/django-js-reverse/issues/29
JS_REVERSE_JS_MINIFY = False


# https://github.com/learningequality/ka-lite/issues/5123
AJAX_ERROR = ugettext_lazy(
    """<p>Sorry, this page is having an unexpected problem - but this error """
    """<strong>is not your fault</strong></p>"""
    """<p>Please don't worry, and select another from 25,000 exercises in here """
    """to continue learning...</p>"""
)

TASTYPIE_CANNED_ERROR = AJAX_ERROR


########################
# Storage and caching
########################

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

# Sessions use the default cache, and we want a local memory cache for that.
CACHE_LOCATION = os.path.realpath(getattr(
    local_settings,
    "CACHE_LOCATION",
    os.path.join(
        USER_DATA_ROOT,
        'cache',
    )
))

CACHES = {
    "default": {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': CACHE_LOCATION,  # this is kind of OS-specific, so dangerous.
        'TIMEOUT': CACHE_TIME,  # should be consistent
        'OPTIONS': {
            'MAX_ENTRIES': getattr(local_settings, "CACHE_MAX_ENTRIES", 5 * 2000)  # 2000 entries=~10,000 files
        },
    }
}

# Prefix the cache with the version string so we don't experience problems with
# updates
KEY_PREFIX = version.VERSION

# Separate session caching from file caching.
SESSION_ENGINE = getattr(
    local_settings, "SESSION_ENGINE", 'django.contrib.sessions.backends.signed_cookies' + (''))

# Expire session cookies after 30 minutes, but extend sessions when there's activity from the user.
SESSION_COOKIE_AGE = 60 * 30     # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True

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


# TODO(benjaoming): Use reverse_lazy for this sort of stuff
LOGIN_URL = "/?login=true"
LOGOUT_URL = "/securesync/api/user/logout/"

# 18 threads seems a sweet spot
CHERRYPY_THREAD_COUNT = getattr(local_settings, "CHERRYPY_THREAD_COUNT", 18)

# PRAGMAs to pass to SQLite when we first open the content DBs for reading. Used mostly for optimizations.
CONTENT_DB_SQLITE_PRAGMAS = []

# Hides content rating
HIDE_CONTENT_RATING = False

########################
# After all settings, but before config packages,
#   import settings from other apps.
#
# This allows app-specific settings to be localized and augment
#   the settings here, while also allowing
#   config packages to override settings.
########################

from kalite.distributed.settings import *
from securesync.settings import *
from fle_utils.chronograph.settings import *
from kalite.facility.settings import *
from kalite.main.settings import *

# Import from applications with problematic __init__.py files
from kalite.legacy.i18n_settings import *
from kalite.legacy.updates_settings import *


KALITE_TEST_RUNNER = "kalite.testing.testrunner.KALiteTestRunner"
TEST_RUNNER = KALITE_TEST_RUNNER

RUNNING_IN_TRAVIS = bool(os.environ.get("TRAVIS"))

TESTS_TO_SKIP = getattr(local_settings, "TESTS_TO_SKIP", ["medium", "long"])  # can be
assert not (set(TESTS_TO_SKIP) - set(["short", "medium", "long"])), "TESTS_TO_SKIP must contain only 'short', 'medium', and 'long'"

AUTO_LOAD_TEST = getattr(local_settings, "AUTO_LOAD_TEST", False)
