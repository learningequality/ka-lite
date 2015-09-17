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

CHANNEL = getattr(settings, "CHANNEL", "khan")

CHANNEL_DATA_PATH = os.path.join(settings.CONTENT_DATA_PATH, CHANNEL)

# Whether we wanna load the perseus assets. Set to False for testing for now.
LOAD_KHAN_RESOURCES = getattr(settings, "LOAD_KHAN_RESOURCES", CHANNEL == "khan")

DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = getattr(settings, "DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP", False)

KHAN_EXERCISES_DIRPATH = os.path.join(settings.STATIC_ROOT, "js", "distributed", "perseus", "ke")

TOPICS_FILEPATHS = {
    CHANNEL: os.path.join(CHANNEL_DATA_PATH, "topics.json")
}
EXERCISES_FILEPATH = os.path.join(CHANNEL_DATA_PATH, "exercises.json")
CONTENT_FILEPATH = os.path.join(CHANNEL_DATA_PATH, "contents.json")
CONTENT_CACHE_FILEPATH = os.path.join(CHANNEL_DATA_PATH, "contents.sqlite")

TOPIC_RECOMMENDATION_DEPTH = 3
