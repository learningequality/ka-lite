import sys
import warnings
from kalite import version
from kalite.shared.exceptions import RemovedInKALite_v016_Error


##############################
# Functions for querying settings
##############################
def package_selected(package_name):
    global CONFIG_PACKAGE
    return bool(CONFIG_PACKAGE) and bool(package_name) and package_name.lower() in CONFIG_PACKAGE

# for extracting assessment item resources
ASSESSMENT_ITEMS_ZIP_URL = "https://learningequality.org/downloads/ka-lite/%s/content/assessment.zip" % version.SHORTVERSION


from .base import *


CHERRYPY_PORT = HTTP_PORT

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
    raise RemovedInKALite_v016_Error("CONFIG_PACKAGE is outdated, use a settings module from kalite.project.settings")

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
    from django.conf import settings
    DEFAULT_ENCODING = settings.DEFAULT_ENCODING

if sys.getdefaultencoding() != DEFAULT_ENCODING:
    reload(sys)
    sys.setdefaultencoding(DEFAULT_ENCODING)
