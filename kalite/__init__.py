import os

from version import *


# suppress warnings here.
try:
    import warnings
    warnings.simplefilter("ignore") # any other filter was ineffecual or threw an error
except:
    pass


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
