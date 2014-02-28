#!/usr/bin/env python
import os, sys, warnings

# We are overriding a few packages (like Django) from the system path.
#   Suppress those warnings
warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path = [PROJECT_PATH, os.path.join(PROJECT_PATH, "../"), os.path.join(PROJECT_PATH, "../python-packages/")] + sys.path

from django.core.management import execute_manager
import kalite.settings


########################
# ZERO CONFIG
########################

if kalite.settings.ZERO_CONFIG:
    # Force all commands to run through our own serve command, which does auto-config if necessary
    # TODO(bcipolli): simplify start scripts, just force everything through kaserve directly.
    if "runserver" in sys.argv:
        sys.argv[sys.argv.index("runserver")] = "kaserve"
    elif "runcherrypyserver" in sys.argv:
        sys.argv[sys.argv.index("runcherrypyserver")] = "kaserve"

########################
# clean_pyc
########################

if len(sys.argv) == 2 and sys.argv[1] == "clean_pyc":
    sys.argv += ["--path", ".."]

########################
# Static files
########################

if "runserver" in sys.argv and "--nostatic" not in sys.argv:
    sys.argv += ["--nostatic"]



if __name__ == "__main__":
    execute_manager(kalite.settings)
