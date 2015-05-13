import logging
import os
import sys
import platform
from fle_utils.settingshelper import import_installed_app_settings
from kalite import version


##############################
# Functions for querying settings
##############################

def package_selected(package_name):
    global CONFIG_PACKAGE
    return bool(CONFIG_PACKAGE) and bool(package_name) and package_name.lower() in CONFIG_PACKAGE


from .base import *

########################
# After all settings, but before config packages,
#   import settings from other apps.
#
# This allows app-specific settings to be localized and augment
#   the settings here, while also allowing
#   config packages to override settings.
########################

# Here is all the old magic crap that should go... /benjaoming

import_installed_app_settings(INSTALLED_APPS, globals())

# TODO(benjaoming): Why on earth is there both a PRODUCTION_PORT and a CHERRYPY_PORT !?
# Mesa confused!
# TODO(benjaoming): Furthermore, this is dependent on kalite.distributed.settings
# so there's no way that kalite.distributed was ever decoupled from kalite
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
ASSESSMENT_ITEMS_RESOURCES_DIR = os.path.join(USER_DATA_ROOT, "content", "khan")
ASSESSMENT_ITEMS_ZIP_URL = "https://learningequality.org/downloads/ka-lite/%s/content/assessment.zip" % version.SHORTVERSION

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

    MIDDLEWARE_CLASSES += ('kalite.distributed.demo_middleware.StopAdminAccess','kalite.distributed.demo_middleware.LinkUserManual','kalite.distributed.demo_middleware.ShowAdminLogin',)


# Force DeprecationWarning to show in DEBUG
if DEBUG:
    import warnings
    warnings.simplefilter('error', DeprecationWarning)

CENTRAL_SERVER_URL = "%s://%s" % (SECURESYNC_PROTOCOL, CENTRAL_SERVER_HOST)


# set the default encoding
# OK, so why do we reload sys? Because apparently sys.setdefaultencoding
# is deleted somewhere at startup. Reloading brings it back.
# see: http://blog.ianbicking.org/illusive-setdefaultencoding.html

# benjaoming: We need to somehow get rid of this as it's discouraged
# http://stackoverflow.com/questions/3828723/why-we-need-sys-setdefaultencodingutf-8-in-a-py-script
# http://ziade.org/2008/01/08/syssetdefaultencoding-is-evil/
try:
    DEFAULT_ENCODING = DEFAULT_ENCODING
except NameError:
    from django.conf.settings import DEFAULT_ENCODING

if sys.getdefaultencoding() != DEFAULT_ENCODING:
    reload(sys)
    sys.setdefaultencoding(DEFAULT_ENCODING)


########################
# Screenshots
########################

SCREENSHOTS_OUTPUT_PATH = os.path.join(USER_DATA_ROOT, "data", "screenshots")
SCREENSHOTS_EXTENSION = ".png"

SCREENSHOTS_DATABASE_NAME = "screenshot-data.sqlite"
SCREENSHOTS_DATABASE_PATH = os.path.join(SCREENSHOTS_OUTPUT_PATH, SCREENSHOTS_DATABASE_NAME)

SCREENSHOTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "data")
SCREENSHOTS_JSON_FILE = os.path.join(SCREENSHOTS_JSON_PATH, 'screenshots.json')
SCREENSHOTS_ROUTER = 'default'
SQLITE3_ENGINE = 'django.db.backends.sqlite3'

if 'screenshots' in sys.argv:
    # use another sqlite3 database for the screenshots
    DATABASES = {
        SCREENSHOTS_ROUTER: {
            "ENGINE": getattr(local_settings, "DATABASE_TYPE", SQLITE3_ENGINE),
            "NAME": SCREENSHOTS_DATABASE_PATH,
            "OPTIONS": {
                "timeout": 60,
            },
        }
    }

