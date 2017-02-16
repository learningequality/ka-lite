import os
import sys

from version import *


__version__ = VERSION

# ROOT_DATA_PATH is *not* where the source files live. It's a place where non-user-writable data files may be written.
if 'KALITE_DIR' in os.environ:
    ROOT_DATA_PATH = os.environ['KALITE_DIR']
else:
    ROOT_DATA_PATH = os.path.join(sys.prefix, 'share', 'kalite')

PACKAGE_PATH = os.path.dirname(__file__)
