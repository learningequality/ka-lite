#!/usr/bin/env python
import glob
import logging
import os
import sys


def clean_pyc(path):
    for root, __, __ in os.walk(os.path.join(path, "..")):
        for pyc_file in glob.glob(os.path.join(root, "*.py[oc]")):
            try:
                os.remove(pyc_file)
            except:
                pass

try:
    import fle_utils  # @UnusedImport
except ImportError:
    sys.stderr.write("You ran manage.py on an incorrect path, use the 'kalite manage ...' command\n")
    sys.exit(-1)

if __name__ == "__main__":
    import warnings
    
    # TODO.. DRY,  is duplicated code, also exists in kalite.settings /benjaoming
    BUILD_INDICATOR_FILE = os.path.join("kalite", "_built.touch")
    BUILT = os.path.exists(BUILD_INDICATOR_FILE)  # whether this installation was processed by the build server

    # We are overriding a few packages (like Django) from the system path.
    #   Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)
    
    ########################
    # kaserve
    ########################

    # Force all commands to run through our own serve command, which does auto-config if necessary
    # TODO(bcipolli): simplify start scripts, just force everything through kaserve directly.
    if "runserver" in sys.argv:
        logging.info("You requested to run runserver; instead, we're funneling you through our 'kaserve' command.")
        sys.argv[sys.argv.index("runserver")] = "kaserve"

    elif "runcherrypyserver" in sys.argv and "stop" not in sys.argv:
        logging.info("You requested to run runcherrypyserver; instead, we're funneling you through our 'kaserve' command.")
        sys.argv[sys.argv.index("runcherrypyserver")] = "kaserve"

    ########################
    # manual clean_pyc
    ########################
    # benjaoming: why are we always doing this, this is horrible for performance
    # ...and before it didn't include python-packages anyways. Can we get to
    # the root cause and implement a better way?
    # http://blog.daniel-watkins.co.uk/2013/02/removing-pyc-files-coda.html
    # Manually clean all pyc files before entering any real codepath
    if not BUILT and "kaserve" in sys.argv:
        clean_pyc(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'kalite'))

    ########################
    # Run it.
    ########################
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
