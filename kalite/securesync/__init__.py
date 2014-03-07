ID_MAX_LENGTH=32
IP_MAX_LENGTH=50

try:
    from version import VERSION
except:
    VERSION = "1.0"

from .devices.__init__ import *
from .engine.__init__ import *
