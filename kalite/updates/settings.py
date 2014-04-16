import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

CONTENT_ROOT   = os.path.realpath(getattr(local_settings, "CONTENT_ROOT", PROJECT_PATH + "/../content/")) + "/"
CONTENT_URL    = getattr(local_settings, "CONTENT_URL", "/content/")

# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = getattr(local_settings, "BACKUP_VIDEO_SOURCE", None)
BACKUP_THUMBNAIL_SOURCE = getattr(local_settings, "BACKUP_THUMBNAIL_SOURCE", None)

UPDATES_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")

# settings for when we're updating the server through Git
GIT_UPDATE_REPO_URL    = getattr(local_settings, "UPDATE_REPO_URL", "https://github.com/learningequality/ka-lite.git")
GIT_UPDATE_BRANCH      = getattr(local_settings, "UPDATE_BRANCH", "master")
GIT_UPDATE_REMOTE_NAME = getattr(local_settings, "GIT_UPDATE_REMOTE_NAME", "updates")
