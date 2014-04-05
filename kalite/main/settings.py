import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Set module settings
#######################

# Used for user logs.  By default, completely off.
#   NOTE: None means no limit (infinite)
USER_LOG_MAX_RECORDS_PER_USER = getattr(local_settings, "USER_LOG_MAX_RECORDS_PER_USER", 1)
USER_LOG_SUMMARY_FREQUENCY = getattr(local_settings, "USER_LOG_SUMMARY_FREQUENCY", (1,"months"))

MAIN_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")