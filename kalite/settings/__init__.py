import sys
import warnings
from kalite import version

from .base import *


CHERRYPY_PORT = HTTP_PORT


# set the default encoding
# OK, so why do we reload sys? Because apparently sys.setdefaultencoding
# is deleted somewhere at startup. Reloading brings it back.
# see: http://blog.ianbicking.org/illusive-setdefaultencoding.html

# benjaoming: We need to somehow get rid of this as it's discouraged
# http://stackoverflow.com/questions/3828723/why-we-need-sys-setdefaultencodingutf-8-in-a-py-script
# http://ziade.org/2008/01/08/syssetdefaultencoding-is-evil/

# benjaoming: If we manage to establish that our usage of JSON files has
# dropped enough, we can get rid of this and stop worrying about memory
# issues.

# See:
# https://github.com/learningequality/ka-lite/issues/3434
try:
    DEFAULT_ENCODING = DEFAULT_ENCODING
except NameError:
    from django.conf import settings
    DEFAULT_ENCODING = settings.DEFAULT_ENCODING

if sys.getdefaultencoding() != DEFAULT_ENCODING:
    reload(sys)
    sys.setdefaultencoding(DEFAULT_ENCODING)
