import sys
import yaml
import os

# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
MAJOR_VERSION = "0"
MINOR_VERSION = "14"
PATCH_VERSION = "dev"
VERSION = "%s.%s.%s" % (MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)
SHORTVERSION = "%s.%s" % (MAJOR_VERSION, MINOR_VERSION)


def load_yaml(file_name):
    """Creates a dictionary from an yaml file.

    Args:
        file_name: The name of the file to be loaded.

    Returns:
        A dictionary structure that reflects the yaml structure.
    """
    file_stream = open(file_name, "r")
    version_object = yaml.load(file_stream)
    return version_object


VERSION_INFO = load_yaml(os.path.join(os.path.dirname(__file__), "version.yaml"))
