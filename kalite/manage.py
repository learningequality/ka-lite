#!/usr/bin/env python
import glob
import logging
import os
import sys
import warnings


def clean_pyc(PROJECT_PATH):
    for root, dirs, files in os.walk(os.path.join(PROJECT_PATH, "..")):
        for pyc_file in glob.glob(os.path.join(root, "*.py[oc]")):
            try:
                os.remove(pyc_file)
            except:
                pass

if __name__ == "__main__":
    import warnings

    BUILD_INDICATOR_FILE = os.path.join(".", "_built.touch")
    BUILT = os.path.exists(BUILD_INDICATOR_FILE)  # whether this installation was processed by the build server

    # We are overriding a few packages (like Django) from the system path.
    #   Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

    # Now build the paths that point to all of the project pieces
    PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
    PROJECT_PYTHON_PATHS = [
        os.path.join(PROJECT_PATH, "..", "python-packages"),
        os.path.join(PROJECT_PATH, ".."),
    ]
    sys.path = [os.path.realpath(p) for p in PROJECT_PYTHON_PATHS] + sys.path

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

    # Manually clean all pyc files before entering any real codepath
    if not BUILT:
        clean_pyc(PROJECT_PATH)


    ########################
    # Run it.
    ########################

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.settings")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
