import os

# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
MAJOR_VERSION = "0"
MINOR_VERSION = "14"
PATCH_VERSION = "dev0"
VERSION = "%s.%s.%s" % (MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)
SHORTVERSION = "%s.%s" % (MAJOR_VERSION, MINOR_VERSION)


def load_yaml(file_name):
    """Creates a dictionary from an yaml file.

    Args:
        file_name: The name of the file to be loaded.

    Returns:
        A dictionary structure that reflects the yaml structure.
    """
    
    # Has to be imported here as version.py is a dependency of setup.py which
    # may be run before dependencies are installed
    import yaml

    with open(file_name, "r") as f:
        return yaml.load(f)


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

    return load_yaml(os.path.join(settings.CONTENT_DATA_PATH, "version.yml"))
