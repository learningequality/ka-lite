import os
import sys

from version import *


__version__ = VERSION

# ROOT_DATA_PATH is *not* where the source files live. It's a place where non-user-writable data files may be written.
ROOT_DATA_PATH = os.path.join(sys.prefix, 'share', 'kalite')
