import os

from django.conf import settings
assert hasattr(settings, "ROOT_UUID_NAMESPACE"), "ROOT_UUID_NAMESPACE setting must be defined to use the securesync module."

ID_MAX_LENGTH=32
IP_MAX_LENGTH=50

try:
    from version import VERSION
except:
    VERSION = "1.0"

from .devices.__init__ import *
from .engine.__init__ import *
