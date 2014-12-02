import os

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
USER_LOG_SUMMARY_FREQUENCY = getattr(local_settings, "USER_LOG_SUMMARY_FREQUENCY", (1,"months"))
