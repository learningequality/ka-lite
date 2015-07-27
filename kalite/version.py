import os

from kalite.shared.utils import open_json_or_yml

# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
# Must be PEP 440 compliant: https://www.python.org/dev/peps/pep-0440/
# Must also be of the form N.N.N for internal use, where N is a non-negative integer

from django.utils.version import get_version

VERSION_TUPLE = (0, 14, 0, "alpha", 0)

MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION = map(str, VERSION_TUPLE[:3])

__version__ = VERSION = get_version(VERSION_TUPLE)

SHORTVERSION = "%s.%s" % (MAJOR_VERSION, MINOR_VERSION)

def VERSION_INFO():
    """
    Load a dictionary of changes between each version. The key of the
    dictionary is the VERSION (i.e. X.X.X), with the value being another dictionary with
    the following keys:

    release_date
    git_commit
    new_features
    bugs_fixed

    """

    # we import settings lazily, since the settings modules depends on
    # this file. Importing it on top will lead to circular imports.
    from django.conf import settings

    return open_json_or_yml(os.path.join(settings.CONTENT_DATA_PATH, "version.yml"))
