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


DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = getattr(settings, "DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP", False)

KHAN_EXERCISES_DIRPATH = os.path.join(settings.STATIC_ROOT, "perseus", "ke")

TOPICS_FILEPATHS = {
    settings.CHANNEL: os.path.join(settings.CHANNEL_DATA_PATH, "topics.json")
}
EXERCISES_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "exercises.json")
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")

TOPIC_RECOMMENDATION_DEPTH = 3
