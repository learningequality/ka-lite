#!/usr/bin/env python
import glob
import logging
import os
import sys


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
    # Run it.
    ########################
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
