"""

benjaoming:

This file replaces caching.settings temporarily until caching.__init__.py has been
cleaned up to not contain references to django post-load modules.


DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY


This will be cleaned up in KA Lite 0.14


"""

try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = getattr(local_settings, "BACKUP_VIDEO_SOURCE", None)
BACKUP_THUMBNAIL_SOURCE = getattr(local_settings, "BACKUP_THUMBNAIL_SOURCE", None)

# This is the standard method... but doesn't work because we cannot load
# kalite.i18n while loading settings because of its __init__.py
# from pkgutil import get_data
# I18N_DATA_PATH = get_data("kalite.i18n", "data")

# settings for when we're updating the server through Git
GIT_UPDATE_REPO_URL = getattr(local_settings, "GIT_UPDATE_REPO_URL", "https://github.com/learningequality/ka-lite.git")
GIT_UPDATE_BRANCH = getattr(local_settings, "GIT_UPDATE_BRANCH", "master")
GIT_UPDATE_REMOTE_NAME = getattr(local_settings, "GIT_UPDATE_REMOTE_NAME", "updates")
