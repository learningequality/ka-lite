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
