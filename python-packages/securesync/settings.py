try:
    import local_settings
except ImportError:
    local_settings = object()

DEBUG = getattr(local_settings, "DEBUG", False)


#######################
# Set module settings
#######################

MIDDLEWARE_CLASSES = (
    "securesync.middleware.RegisteredCheck",
    "securesync.middleware.DBCheck",
)

SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https" if not DEBUG else "http")

SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", None)  # default: don't throttle syncing

SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 100)  # 100 records per http request

# Here, None === no limit
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", None)

SHOW_DELETED_OBJECTS = getattr(local_settings, "SHOW_DELETED_OBJECTS", False)

DEBUG_ALLOW_DELETIONS = getattr(local_settings, "DEBUG_ALLOW_DELETIONS", False)
