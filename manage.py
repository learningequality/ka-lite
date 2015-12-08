#!/usr/bin/env python
import logging
import os
import sys

# In case we have not defined an environment, try to see if manage.py is run
# from the source tree and add python-packages to the system path
if 'KALITE_DIR' not in os.environ:
    if os.path.exists('./python-packages'):
        sys.path = ['./python-packages'] + sys.path

try:
    import fle_utils  # @UnusedImport
except ImportError:
    sys.stderr.write("You ran manage.py on an incorrect path, use the 'kalite manage ...' command\n")
    sys.exit(-1)

if __name__ == "__main__":
    import warnings

    # We are overriding a few packages (like Django) from the system path.
    #   Suppress those warnings
    warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

    ########################
    # Run it.
    ########################
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kalite.project.settings.default")

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
