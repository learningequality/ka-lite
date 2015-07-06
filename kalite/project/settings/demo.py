"""
This module is for running a demo server (internal FLE purpose mainly).
To use it, run kalite with --settings=kalite.project.settings.demo or
set then environment variable DJANGO_SETTINGS_MODULE to
'kalite.project.settings.demo'.
"""
from .base import *  # @UnusedWildImport

CENTRAL_SERVER_HOST = getattr(local_settings, "CENTRAL_SERVER_HOST", "staging.learningequality.org")
SECURESYNC_PROTOCOL = getattr(local_settings, "SECURESYNC_PROTOCOL", "http")
CENTRAL_SERVER_URL = "%s://%s" % (SECURESYNC_PROTOCOL, CENTRAL_SERVER_HOST)
DEMO_ADMIN_USERNAME = getattr(local_settings, "DEMO_ADMIN_USERNAME", "admin")
DEMO_ADMIN_PASSWORD = getattr(local_settings, "DEMO_ADMIN_PASSWORD", "pass")

MIDDLEWARE_CLASSES += (
    'kalite.distributed.demo_middleware.StopAdminAccess',
    'kalite.distributed.demo_middleware.LinkUserManual',
    'kalite.distributed.demo_middleware.ShowAdminLogin',
)
