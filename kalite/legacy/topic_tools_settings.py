"""

benjaoming:

This file replaces topic_tools.settings temporarily until topic_tools.__init__.py has been
cleaned up to not contain references to django post-load modules.


DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY


This will be cleaned up in KA Lite 0.14


"""

import os

try:
    from kalite import local_settings
except ImportError:
    local_settings = object()

from kalite.settings.base import STATIC_ROOT, STATIC_URL

#######################
# Set module settings
#######################
DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = getattr(local_settings, "DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP", False)

KHAN_EXERCISES_RELPATH = os.path.join(STATIC_URL, "perseus", "ke")

KHAN_EXERCISES_DIRPATH = os.path.join(STATIC_ROOT, "perseus", "ke")
