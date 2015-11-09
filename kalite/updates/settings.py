"""

New settings pattern

See:
https://github.com/learningequality/ka-lite/issues/4054
https://github.com/learningequality/ka-lite/issues/3757

All settings for the updates app should be defined here, they can
only on django.conf.settings
"""
import os
from django.conf import settings

VIDEO_DOWNLOAD_QUEUE_FILE = os.path.join(settings.USER_DATA_ROOT, "videos_to_download.json")
