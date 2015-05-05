import sys
import yaml

# THIS IS USED BY settings.py.  NEVER import settings.py here; hard-codes only!
MAJOR_VERSION = "0"
MINOR_VERSION = "14"
PATCH_VERSION = "dev"
VERSION = "%s.%s.%s" % (MAJOR_VERSION, MINOR_VERSION, PATCH_VERSION)
SHORTVERSION = "%s.%s" % (MAJOR_VERSION, MINOR_VERSION)


def load_yaml(file_name, current_version, yaml_file_version_mapping):
    """Creates a dictionary from an yaml file.

    Args:
        file_name: The name of the file to be loaded.
        current_version: The current version of KA Lite.
        yaml_file_version_mapping: The 'VERSION' string to be replaced by the actual KA Lite version.

    Returns:
        A dictionary structure that reflects the yaml structure.

    Raises:
        IOError: If the file doesn't exist or can't be opened.
    """
    try:
        file_stream = open(file_name, "r")
        version_object = yaml.load(file_stream)
        version_object[current_version] = version_object[yaml_file_version_mapping]
        del version_object[yaml_file_version_mapping]
        return version_object
    except IOError:
        sys.stderr.write("Error: The file with name: '%s' doesn't exist or couldn't be open.\n" % (file_name))
        sys.exit(1)


VERSION_INFO = load_yaml(os.path.join(os.path.dirname(__file__), "version.yaml"), VERSION, "VERSION")