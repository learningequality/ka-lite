"""
Helper stuff for compatibility issues
"""

try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6
    from ordereddict import OrderedDict  # @UnusedImport
