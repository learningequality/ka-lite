import os
import uuid


from django.http import HttpRequest


try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


########################
# Functions, for support
########################

# This defaults to 8008, which is also the default of kalite.__main__ which should
# always set KALITE_LISTEN_PORT
HTTP_PORT = os.environ.get('KALITE_LISTEN_PORT', 8008)

# This can be configured differently in case proxy is used. When communicating
# kalite's port, always use this variable, not HTTP_PORT.
USER_FACING_PORT = HTTP_PORT


##############################
# Django settings
##############################


TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), "templates"),)


##############################
# KA Lite settings
##############################

# Note: this MUST be hard-coded for backwards-compatibility reasons.
ROOT_UUID_NAMESPACE = uuid.UUID("a8f052c7-8790-5bed-ab15-fe2d3b1ede41")  # print uuid.uuid5(uuid.NAMESPACE_URL, "https://kalite.adhocsync.com/")

CENTRAL_SERVER = getattr(local_settings, "CENTRAL_SERVER", False)
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "learningequality.org")
SECURESYNC_PROTOCOL = getattr(local_settings, "SECURESYNC_PROTOCOL", "https")
CENTRAL_SERVER_HOST = getattr(local_settings, "CENTRAL_SERVER_HOST", "kalite.%s" % CENTRAL_SERVER_DOMAIN)
CENTRAL_SERVER_URL = "%s://%s" % (SECURESYNC_PROTOCOL, CENTRAL_SERVER_HOST)
CENTRAL_WIKI_URL = getattr(local_settings, "CENTRAL_WIKI_URL", "http://kalitewiki.%s/" % CENTRAL_SERVER_DOMAIN)

PDFJS = getattr(local_settings, "PDFJS", True)

########################
# Exercise AB-testing
########################
FIXED_BLOCK_EXERCISES = getattr(local_settings, 'FIXED_BLOCK_EXERCISES', 0)
STREAK_CORRECT_NEEDED = getattr(local_settings, 'STREAK_CORRECT_NEEDED', 8)

########################
# Video AB-testing
########################
POINTS_PER_VIDEO = getattr(local_settings, 'POINTS_PER_VIDEO', 750)


########################
# Zero-config options
########################

ZERO_CONFIG = getattr(local_settings, "ZERO_CONFIG", False)

# With zero config, no admin (by default)
INSTALL_ADMIN_USERNAME = getattr(local_settings, "INSTALL_ADMIN_USERNAME", None)
INSTALL_ADMIN_PASSWORD = getattr(local_settings, "INSTALL_ADMIN_PASSWORD", None)
assert bool(INSTALL_ADMIN_USERNAME) + bool(INSTALL_ADMIN_PASSWORD) != 1, "Must specify both admin username and password, or neither."


########################
# Security
########################

LOCKDOWN = getattr(local_settings, "LOCKDOWN", False)


# TODO(benjaoming): Get rid of this
import mimetypes

########################
# Font setup
########################

# Add additional mimetypes to avoid errors/warnings
mimetypes.add_type("font/opentype", ".otf", True)
