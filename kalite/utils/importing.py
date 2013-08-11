"""
Contains helper functions for importing modules.
"""

import os, glob

def import_all_from(path, locals, globals, pattern="*", exclude_special_modules=True):
    """Import * from all the .py files in a particular directory.
    
    This is currently only used for auto-import of test suites, but may be useful elsewhere.
    """

    # load the names of all the modules in the directory
    module_names = [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(path) + "/" + pattern + ".py")]

    # effectively do a `from <module> import *` for all the modules
    for module_name in module_names:

        # skip special modules, if specified
        if exclude_special_modules and module_name.startswith("_"):
            continue

        # import the module by name, passing globals so it can make use of Django stuff
        # http://www.diveintopython.net/functional_programming/dynamic_import.html
        module = __import__(module_name, globals=globals)

        # bring all the contents of the module into the original namespace (ala `from ... import *`)
        for name in dir(module):
            locals[name] = getattr(module, name)