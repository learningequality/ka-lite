"""
This module is for running a central server. To use it, run kalite with
--settings=kalite.project.settings.central_server or set then environment
variable DJANGO_SETTINGS_MODULE to 'kalite.project.settings.central_server'.
"""
from .base import *  # @UnusedWildImport

# Used to have two very different use cases in the same codebase :)
CENTRAL_SERVER = True