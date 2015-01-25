#!/usr/bin/env python
import os
import sys
import warnings

# Q: Why was this moved?
# A: Because it doesn't match a normal Django project layout to put the
#    manage.py script in the project package and leads to unnecessary
#    mangling of the project path (see below)

warning_txt = (
    "You should not run kalite/manage.py, it's gone in kalite 0.14. Instead, "
    "use the 'kalite' command."
)

# Explicitly print it because warnings are suppressed
print warning_txt

warnings.warn(
    warning_txt,
    DeprecationWarning,
    stacklevel=1
)

# Add the parent directory to the path because we're running manage.py from
# a non-conventional location

# Now build the paths that point to all of the project pieces
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path = [os.path.join(PROJECT_PATH, ".."), os.path.join(PROJECT_PATH, "..", "python-packages")] + sys.path

# Now build the paths that point to all of the project pieces
my_path = os.path.dirname(os.path.realpath(__file__))

execfile(os.path.join(my_path, "..", "manage.py"))