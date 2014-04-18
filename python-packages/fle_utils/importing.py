"""
Contains helper functions for importing modules.
"""

import glob
import os
import inspect


def import_all_child_modules():
    current_frame = inspect.currentframe()
    caller_locals = current_frame.f_back.f_locals
    caller_globals = current_frame.f_back.f_globals
    caller_path = os.path.dirname(caller_locals["__file__"])

    return import_all_from(caller_path, caller_locals, caller_globals)


def import_all_from(path, locals, globals, pattern="*"):
    """
    Import * from all the .py files in a particular directory whose names match a particular pattern.
    """
    # load the names of all the modules in the directory
    py_modules = [os.path.basename(f)[:-3] for f in glob.glob("%s/%s.py" % (path, pattern))]
    dir_modules = [os.path.basename(f) for f in glob.glob("%s/%s" % (path, pattern)) if os.path.isdir(f) and os.path.exists(os.path.join(f, '__init__.py'))]
    module_names = py_modules + dir_modules

    # effectively do a `from <module> import *` for all the modules
    for module_name in module_names:

        # skip special modules
        if module_name.startswith("_"):
            continue

        # import the module by name, passing globals so it can make use of Django stuff
        # http://www.diveintopython.net/functional_programming/dynamic_import.html
        module = __import__(module_name, globals=globals)

        # bring all the contents of the module into the original namespace (ala `from ... import *`)
        for name in dir(module):
            if name.startswith("_"):
                continue
            locals[name] = getattr(module, name)
