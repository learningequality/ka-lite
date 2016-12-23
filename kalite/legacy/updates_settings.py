"""

benjaoming:

This file replaces caching.settings temporarily until caching.__init__.py has been
cleaned up to not contain references to django post-load modules.


DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY


This will be cleaned up in KA Lite 0.14


"""


#######################
# Set module settings
#######################

# Should be a function that receives a video file (youtube ID), and returns a URL to a video stream
BACKUP_VIDEO_SOURCE = None
BACKUP_THUMBNAIL_SOURCE = None
