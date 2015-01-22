"""
Wrapper for loading Handlebars templates from "hbtemplates" directories in
INSTALLED_APPS packages. Based in part on django/template/loaders/app_directories.py
"""

import glob
import os
import re
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils._os import safe_join
from django.utils.importlib import import_module


# At compile time, cache the directories to search.
fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
app_hbtemplates_dirs = []
for app in settings.INSTALLED_APPS:
    try:
        mod = import_module(app)
    except ImportError, e:
        raise ImproperlyConfigured('ImportError %s: %s' % (app, e.args[0]))
    template_dir = os.path.join(os.path.dirname(mod.__file__), 'hbtemplates')
    if os.path.isdir(template_dir):
        app_hbtemplates_dirs.append(template_dir.decode(fs_encoding))

# It won't change, so convert it to a tuple to save memory.
app_hbtemplates_dirs = tuple(app_hbtemplates_dirs)


def get_template_module_paths(module_name):
    """
    Returns the absolute paths to HB templates under *module_name* subdirectories,
    searching through the "hbtemplates" dirs of every installed app.
    """

    paths = []

    for template_dir in app_hbtemplates_dirs:
        try:
            directory = safe_join(template_dir, module_name)
            paths += glob.glob(safe_join(directory, "*.handlebars"))
        except UnicodeDecodeError:
            # The template dir name was a bytestring that wasn't valid UTF-8.
            raise
        except ValueError:
            # The joined path was located outside of template_dir.
            pass

    return paths


def load_template_sources(module_name):

    templates = []

    for filepath in get_template_module_paths(module_name):
        # REF: http://stackoverflow.com/a/14334768/845481
        # How to split a dos path into its components in Python
        # On Windows, we might encounter path like c:\python2.7/python.exe, so using `normpath`.
        filepath = os.path.normpath(filepath)
        # Use specific path separator for the OS.
        template_name = filepath.split(os.sep)[-1].split(".handlebars")[0]
        try:
            with open(filepath) as f:
                # load the template text
                template_text = f.read()
                # collapse extraneous whitespace to a single space
                template_text = re.sub("\s+", " ", template_text)
                # add this template to the list
                templates.append({
                    "name": "%s/%s" % (module_name, template_name),
                    "raw": template_text,
                })
        except IOError:
            pass

    return templates
