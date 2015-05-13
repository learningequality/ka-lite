import os
import sys

from version import *


# Where all data is stored in a kalite installation, relative to sys.prefix
# If running kalite from source dir, you can disregard it.
ROOT_DATA_PATH = os.path.join(sys.prefix, 'share/kalite')


# TODO: Burn down this function, the name is weird, it just checks if a
# database exists... not really significant enough to put it in kalite.__init__
def is_installed():
    """Returns True if KA Lite is installed."""

    from django.conf import settings

    if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
        return os.path.exists(settings.DATABASES["default"]["NAME"])  # this is the db filepath for SQLite
    else:
        # TODO(bcipolli): use django raw connection to test; something like:
        # from django.db import connection
        # try:
        #     connection.introspection.table_names()
        #     return True
        # except:
        #     return False
        return True
