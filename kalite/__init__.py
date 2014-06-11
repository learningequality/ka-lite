import os

from django.conf import settings

from version import *


# suppress warnings here.
try:
    import warnings
    warnings.simplefilter("ignore") # any other filter was ineffecual or threw an error
except:
    pass


def is_installed():
    """Returns True if KA Lite is installed."""

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
