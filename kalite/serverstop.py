#!/usr/bin/env python2

import os
import sys

# Set up the paths
script_dir = os.path.dirname(os.path.realpath(__file__))
python_packages_dir = script_dir + "/../python-packages/"
sys.path = sys.path + [ python_packages_dir]

# Import the server
from django_cherrypy_wsgiserver.cherrypyserver import stop_server

# Call stop!
pid_file = os.path.realpath(script_dir + "/runcherrypyserver.pid")
stop_server(pid_file)
