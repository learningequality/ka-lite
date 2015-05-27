from __future__ import print_function

import json
import os
import yaml

from django.core.management.base import NoArgsCommand

BLACKLISTED_YAML_FILES = [
    ".travis.yml",
    "circle.yml"
]


class Command(NoArgsCommand):

    def handle_noargs(*args, **kwargs):
        # avoid using django.conf.settings, for that sweet fast startup
        # time
        project_root = os.environ.get("KALITE_DIR")
        for root, _, files in os.walk(project_root):
            for f in files:
                full_name = os.path.join(root, f)
                if (full_name.endswith(".yml") and
                    "node_modules" not in root and
                    f not in BLACKLISTED_YAML_FILES):
                    print(full_name)
                    yml_to_json(full_name)


def yml_to_json(filename):
    """Convert a .yml file into a json file and save it to the same
    directory.
    """
    jsonfilename = "{0}.json".format(*os.path.splitext(filename))

    with open(filename, "r") as f:
        contents = yaml.load(f)

    with open(jsonfilename, "w") as f:
        json.dump(contents, f)
