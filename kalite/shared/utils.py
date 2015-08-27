import os

def open_json_or_yml(file_name):
    """Try to load either the JSON or YAML version of a file.

    If DEBUG is True, try to load the file with a yml prefix. If
    DEBUG = False, try to load the json version first.

    Args:
        file_name: The name of the file to be loaded.

    Returns:
        A dictionary structure that reflects the yaml structure.

    """

    try:
        import json
        # ensure that it has the json extension
        json_file = "{0}.json".format(*os.path.splitext(file_name))
        with open(json_file, "r") as f:
            return json.load(f)
    except IOError:
        import yaml
        # ensure that it has the yml extension
        yml_file = "{0}.yml".format(*os.path.splitext(file_name))
        with open(yml_file, "r") as f:
            return yaml.load(f)
