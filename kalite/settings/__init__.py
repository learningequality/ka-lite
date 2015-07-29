import sys
import warnings
from kalite import version
from kalite.shared.warnings import RemovedInKALite_v015_Warning


warnings.warn(
    "Wrong settings module imported! Please do not import kalite.settings "
    "directly. Instead, import kalite.project.settings.base",
    RemovedInKALite_v015_Warning
)


##############################
# Functions for querying settings
##############################
def package_selected(package_name):
    global CONFIG_PACKAGE
    return bool(CONFIG_PACKAGE) and bool(package_name) and package_name.lower() in CONFIG_PACKAGE

# for extracting assessment item resources
ASSESSMENT_ITEMS_ZIP_URL = "https://learningequality.org/downloads/ka-lite/%s/content/assessment.zip" % version.SHORTVERSION


from .base import *


CHERRYPY_PORT = getattr(local_settings, "CHERRYPY_PORT", PRODUCTION_PORT)

########################
# IMPORTANT: Do not add new settings below this line
#
# Everything that follows is overriding default settings, depending on CONFIG_PACKAGE
########################

# A deprecated setting that shouldn't be used
CONFIG_PACKAGE = getattr(local_settings, "CONFIG_PACKAGE", [])
if isinstance(CONFIG_PACKAGE, basestring):
    CONFIG_PACKAGE = [CONFIG_PACKAGE]
CONFIG_PACKAGE = [cp.lower() for cp in CONFIG_PACKAGE]


if CONFIG_PACKAGE:
    warnings.warn(
        "CONFIG_PACKAGE is outdated, use a settings module from kalite.project.settings",
        RemovedInKALite_v015_Warning
    )

# Config for Raspberry Pi distributed server
if package_selected("RPi"):

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

    DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = True
    USING_RASPBERRY_PI = True


if package_selected("nalanda"):
    TURN_OFF_MOTIVATIONAL_FEATURES = True
    RESTRICTED_TEACHER_PERMISSIONS = True
    FIXED_BLOCK_EXERCISES = 5
    QUIZ_REPEATS = 3
    UNIT_POINTS = 2000

if package_selected("UserRestricted"):
    LOG.info("UserRestricted package selected.")
    DISABLE_SELF_ADMIN = True  # hard-code facility app setting.


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
    from django.conf.settings import DEFAULT_ENCODING  # @UnresolvedImport

if sys.getdefaultencoding() != DEFAULT_ENCODING:
    reload(sys)
    sys.setdefaultencoding(DEFAULT_ENCODING)
