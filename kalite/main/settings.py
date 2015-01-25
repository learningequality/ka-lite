import os
import json

try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.staticfiles",
    "south",
    "fle_utils.django_utils",  # templatetags
    "kalite.facility",  # must come first, all other apps depend on this one.
    "kalite.i18n",  # get_video_id
    "kalite.topic_tools",  # For finding and validating exercises / videos
    "kalite.testing",
    "securesync",
)

#######################
# Set module settings
#######################

# Used for user logs.  By default, completely off.
#   NOTE: None means no limit (infinite)
USER_LOG_MAX_RECORDS_PER_USER = getattr(local_settings, "USER_LOG_MAX_RECORDS_PER_USER", 1)
USER_LOG_SUMMARY_FREQUENCY = getattr(local_settings, "USER_LOG_SUMMARY_FREQUENCY", (1,"day"))
CHANNEL = getattr(local_settings, "CHANNEL", "khan")
CONTENT_DATA_PATH = getattr(local_settings, "CONTENT_DATA_PATH", os.path.join(os.path.dirname(__file__), "../../data"))
CONTENT_DATA_URL = getattr(local_settings, "CONTENT_DATA_URL", "/data/")
CHANNEL_DATA_PATH = os.path.join(CONTENT_DATA_PATH, CHANNEL)
try:
    CHANNEL_DATA = json.load(open(os.path.join(CHANNEL_DATA_PATH, "channel_data.json"), 'r'))
except IOError:
    CHANNEL_DATA = {}

# Whether we wanna load the perseus assets. Set to False for testing for now.
LOAD_KHAN_RESOURCES = getattr(local_settings, "LOAD_KHAN_RESOURCES", CHANNEL == "khan")
