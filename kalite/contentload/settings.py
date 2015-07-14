"""

New settings pattern

See:
https://github.com/learningequality/ka-lite/issues/4054
https://github.com/learningequality/ka-lite/issues/3757

All settings for the topic_tools app should be defined here, they can
only on django.conf.settings
"""
import os
from django.conf import settings


# Special setting for Khan Academy content
KHAN_CONTENT_PATH = os.path.join(settings.CONTENT_ROOT, "khan")
if not os.path.exists(KHAN_CONTENT_PATH):
    os.mkdir(KHAN_CONTENT_PATH)
