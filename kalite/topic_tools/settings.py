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

CONTENT_DATABASE_ROOT = os.path.join(settings.USER_DATA_ROOT, "content_databases")
if not os.path.exists(CONTENT_DATABASE_ROOT):
    os.mkdir(CONTENT_DATABASE_ROOT)

CONTENT_DATABASE_PATH = os.path.join(CONTENT_DATABASE_ROOT, "content_{channel}_{language}.sqlite")

CHANNEL = getattr(settings, "CHANNEL", "khan")

CHANNEL_DATA_PATH = os.path.join(settings.CONTENT_DATA_PATH, CHANNEL)

KHAN_EXERCISES_DIRPATH = os.path.join(settings.STATIC_ROOT, "js", "distributed", "perseus", "ke")

TOPIC_RECOMMENDATION_DEPTH = 3
