try:
    import local_settings
except ImportError:
    local_settings = object()


########################
# Django dependencies
########################

INSTALLED_APPS = (
    "django.contrib.auth",  # co-exists with Django auth
    "django.contrib.sessions",  # logged in user stored within session object
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "south",
    "fle_utils.config",  # Settings used for default_facility
    "fle_utils.django_utils",  # templatetags
    "securesync",  # must be above, for dependency on RegisteredCheck middleware
    "kalite.i18n",  # needed for default_language   TODO: make default_language part of facility, use settings.LANGUAGE
    "kalite.main", # needed for UserLog  TODO: move UserLog into main app, connect here as signal listeners
    "kalite.testing",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "fle_utils.django_utils.middleware.GetNextParam",  # adds request.next parameter
    __package__ + ".middleware.AuthFlags",  # this must come first in app-dependent middleware--many others depend on it.
    __package__ + ".middleware.FacilityCheck",
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",  # used by distributed to authenticate admin (django) user
    "django.core.context_processors.request",  # expose request object within templates
    __package__ + ".custom_context_processors.custom",  # for enabling a 'restricted' user mode for self-admin of user accounts
)


#######################
# Set module settings
#######################

# Default facility name
INSTALL_FACILITY_NAME = getattr(local_settings, "INSTALL_FACILITY_NAME", None)  # default to None, so can be translated to latest language at runtime.

# None means, use full hashing locally--turn off the password cache
PASSWORD_ITERATIONS_TEACHER = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER", None)
PASSWORD_ITERATIONS_STUDENT = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT", None)
assert PASSWORD_ITERATIONS_TEACHER is None or PASSWORD_ITERATIONS_TEACHER >= 1, "If set, PASSWORD_ITERATIONS_TEACHER must be >= 1"
assert PASSWORD_ITERATIONS_STUDENT is None or PASSWORD_ITERATIONS_STUDENT >= 1, "If set, PASSWORD_ITERATIONS_STUDENT must be >= 1"

# This should not be set, except in cases where additional security is desired.
PASSWORD_ITERATIONS_TEACHER_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_TEACHER_SYNCED", 5000)
PASSWORD_ITERATIONS_STUDENT_SYNCED = getattr(local_settings, "PASSWORD_ITERATIONS_STUDENT_SYNCED", 2500)
assert PASSWORD_ITERATIONS_TEACHER_SYNCED >= 5000, "PASSWORD_ITERATIONS_TEACHER_SYNCED must be >= 5000"
assert PASSWORD_ITERATIONS_STUDENT_SYNCED >= 2500, "PASSWORD_ITERATIONS_STUDENT_SYNCED must be >= 2500"

PASSWORD_CONSTRAINTS = getattr(local_settings, "PASSWORD_CONSTRAINTS", {
    'min_length': getattr(local_settings, 'PASSWORD_MIN_LENGTH', 6),
})


DISABLE_SELF_ADMIN = getattr(local_settings, "DISABLE_SELF_ADMIN", False)  #
