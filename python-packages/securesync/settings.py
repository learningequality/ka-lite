try:
    import local_settings
except ImportError:
    local_settings = object()

DEBUG = getattr(local_settings, "DEBUG", False)



##############################
# Django settings
##############################

# TODO(bcipolli): change these to "login" and "logout", respectively, if/when
#  we migrate to a newer version of Django.  Older versions require these
#  to be set if using the login_required decorator.
LOGIN_URL = "/securesync/login/"
LOGOUT_URL = "/securesync/logout/"

INSTALLED_APPS = (
    "django.contrib.auth",  # central server login still embedded here
    "django.contrib.sessions",  # install_validated
    "django.contrib.messages",
    "django_extensions", # needed for clean_pyc (testing)
    "fle_utils.config",  # Settings (private_key)
    "fle_utils.chronograph",  # force_job
    "fle_utils.django_utils",  # templatetags
)


MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "securesync.middleware.RegisteredCheck",
    "securesync.middleware.DBCheck",
)

#######################
# Set module settings
#######################

SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https" if not DEBUG else "http")

SYNCING_THROTTLE_WAIT_TIME = getattr(local_settings, "SYNCING_THROTTLE_WAIT_TIME", None)  # default: don't throttle syncing

SYNCING_MAX_RECORDS_PER_REQUEST = getattr(local_settings, "SYNCING_MAX_RECORDS_PER_REQUEST", 100)  # 100 records per http request

# Here, None === no limit
SYNC_SESSIONS_MAX_RECORDS = getattr(local_settings, "SYNC_SESSIONS_MAX_RECORDS", 10)

SHOW_DELETED_OBJECTS = getattr(local_settings, "SHOW_DELETED_OBJECTS", False)

DEBUG_ALLOW_DELETIONS = getattr(local_settings, "DEBUG_ALLOW_DELETIONS", False)
