import os, glob

# load the names of all the test modules in the current directory
module_names = [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + "/*test*.py")]

# effectively do a `from <module> import *` for all the test modules, so all tests will be included
for module_name in module_names:

    # import the module by name, passing globals so it can make use of Django stuff
    # http://www.diveintopython.net/functional_programming/dynamic_import.html
    module = __import__(module_name, globals=globals())

    # bring all the contents of the module into the local namespace (ala `from ... import *`)
    for name in dir(module):
        locals()[name] = getattr(module, name)

