import getpass
import hashlib
import os
import sys
import tempfile
import time
import uuid
import version  # in danger of a circular import.  NEVER add settings stuff there--should all be hard-coded.

try:
    import local_settings
except ImportError:
    local_settings = object()

DEBUG = getattr(local_settings, "DEBUG", False)


########################
# Functions, for support
########################

def USER_FACING_PORT():
    global PROXY_PORT
    global PRODUCTION_PORT
    return PROXY_PORT or PRODUCTION_PORT


##############################
# Django settings
##############################

# TODO(bcipolli): change these to "login" and "logout", respectively, if/when
#  we migrate to a newer version of Django.  Older versions require these
#  to be set if using the login_required decorator.
LOGIN_URL = "/securesync/login/"
LOGOUT_URL = "/securesync/logout/"

INSTALLED_APPS = (
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "fle_utils.config",
    "fle_utils.chronograph",
    "fle_utils.django_utils",  # templatetags
    "fle_utils.handlebars",
    "fle_utils.backbone",
    "kalite.facility",  # must come first, all other apps depend on this one.
    "kalite.control_panel",  # in both apps
    "kalite.coachreports",  # in both apps; reachable on central via control_panel
    "kalite.django_cherrypy_wsgiserver",  # API endpoint for PID
    "kalite.i18n",  #
    "kalite.contentload",  # content loading interactions
    "kalite.topic_tools",  # Querying topic tree
    "kalite.main", # in order for securesync to work, this needs to be here.
    "kalite.playlist",
    "kalite.testing",
    "kalite.updates",  #
    "kalite.student_testing",
    "kalite.caching",
    "kalite.store",
    "kalite.remoteadmin",  # needed for remote connection
    "securesync",  # needed for views that probe Device, Zone, even online status (BaseClient)
    "kalite.ab_testing",
    "kalite.dynamic_assets",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",  # a bunch of shortcuts used by distributed
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    __package__ + ".middleware.LockdownCheck",
    "student_testing.middleware.ExamModeCheck",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",  # expose request object within templates
    __package__ + ".custom_context_processors.custom",  #
)

TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)

if DEBUG:
    INSTALLED_APPS += ("django_snippets",)   # used in contact form and (debug) profiling middleware
    TEMPLATE_CONTEXT_PROCESSORS += ("django.core.context_processors.debug",)  # used in conjunction with toolbar to show query information


##############################
# KA Lite settings
##############################

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
SECURESYNC_PROTOCOL = getattr(local_settings, "SECURESYNC_PROTOCOL", "https" if not DEBUG else "http")
CENTRAL_SERVER_HOST   = getattr(local_settings, "CENTRAL_SERVER_HOST",   ("adhoc.%s:7007" if DEBUG else "kalite.%s") % CENTRAL_SERVER_DOMAIN)
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)

KHAN_EXERCISES_DIRPATH = os.path.join(os.path.dirname(__file__), "static", "khan-exercises")

########################
# Exercise AB-testing
########################
FIXED_BLOCK_EXERCISES = getattr(local_settings, 'FIXED_BLOCK_EXERCISES', 0)
STREAK_CORRECT_NEEDED = getattr(local_settings, 'STREAK_CORRECT_NEEDED', 8)

########################
# Video AB-testing
########################
POINTS_PER_VIDEO = getattr(local_settings, 'POINTS_PER_VIDEO', 750)

########################
# Ports & Accessibility
########################

PRODUCTION_PORT = getattr(local_settings, "PRODUCTION_PORT", 8008)

#proxy port is used by nginx and is used by Raspberry Pi optimizations
PROXY_PORT = getattr(local_settings, "PROXY_PORT", None)

HTTP_PROXY     = getattr(local_settings, "HTTP_PROXY", None)
HTTPS_PROXY     = getattr(local_settings, "HTTPS_PROXY", None)


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
CACHE_NAME = getattr(local_settings, "CACHE_NAME", None)  # without a cache defined, None is fine

# Cache is activated in every case,
#   EXCEPT: if CACHE_TIME=0
if CACHE_TIME != 0:  # None can mean infinite caching to some functions
    KEY_PREFIX = version.VERSION_INFO[version.VERSION]["git_commit"][0:6]  # new cache for every build
    if 'CACHES' not in locals():
        CACHES = {}

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


########################
# RPi features
########################

# Clock Setting disabled by default unless overriden.
# Note: This will only work on Linux systems where the server is running as root.
ENABLE_CLOCK_SET = False


########################
# Zero-config options
########################

ZERO_CONFIG   = getattr(local_settings, "ZERO_CONFIG", False)

# With zero config, no admin (by default)
INSTALL_ADMIN_USERNAME = getattr(local_settings, "INSTALL_ADMIN_USERNAME", None)
INSTALL_ADMIN_PASSWORD = getattr(local_settings, "INSTALL_ADMIN_PASSWORD", None)
assert bool(INSTALL_ADMIN_USERNAME) + bool(INSTALL_ADMIN_PASSWORD) != 1, "Must specify both admin username and password, or neither."


########################
# Security
########################

LOCKDOWN = getattr(local_settings, "LOCKDOWN", False)
