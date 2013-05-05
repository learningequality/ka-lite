import json
import os

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

def localor(setting_name, default_val):
    """Returns local_settings version if it exists (and is non-empty), otherwise uses default value"""
    return hasattr(local_settings, setting_name) and getattr(local_settings, setting_name) or default_val
    
DEBUG          = localor("DEBUG", False)
TEMPLATE_DEBUG = localor("TEMPLATE_DEBUG", False)

INTERNAL_IPS   = localor("INTERNAL_IPS", ("127.0.0.1",))

CENTRAL_SERVER = localor("CENTRAL_SERVER", False)

ADMINS         = localor("ADMINS", ( ("Jamie Alexandre", "jamalex@gmail.com"), ) )

MANAGERS       = localor("MANAGERS", ADMINS)

PROJECT_PATH   = localor("PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))

LOCALE_PATHS   = localor("LOCALE_PATHS", (PROJECT_PATH + "/../locale",))

DATABASES      = localor("DATABASES", {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME"  : localor("DATABASE_PATH", PROJECT_PATH + "/database/data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

DATA_PATH      = localor("DATA_PATH", PROJECT_PATH + "/static/data/")

CONTENT_ROOT   = localor("CONTENT_ROOT", PROJECT_PATH + "/../content/")
CONTENT_URL    = localor("CONTENT_URL", "/content/")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = localor("TIME_ZONE", "America/Los_Angeles")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = localor("LANGUAGE_CODE", "en-us")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = localor("USE_I18N", True)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N       = localor("USE_L10N", False)

MEDIA_ROOT     = localor("MEDIA_ROOT", PROJECT_PATH + "/static/")
MEDIA_URL      = localor("MEDIA_URL", "/static/")
STATIC_URL     = localor("STATIC_URL", "/static/")

# Make this unique, and don't share it with anybody.
SECRET_KEY     = localor("SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

TEMPLATE_DIRS  = localor("TEMPLATE_DIRS", (PROJECT_PATH + "/templates",))


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "main.custom_context_processors.custom",
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
#     "django.template.loaders.eggs.Loader",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.locale.LocaleMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.GetNextParam",
)

ROOT_URLCONF = "kalite.urls"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.humanize",
    "django.contrib.messages",
    "south",
    "chronograph",
    "django_cherrypy_wsgiserver",
    "securesync",
    "config",
    "main",
    "faq",
    "loadtesting",
)

if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_extensions",)

CENTRAL_SERVER_HOST = localor("CENTRAL_SERVER_HOST", "https://kalite.adhocsync.com/")

CENTRAL_SERVER = localor("CENTRAL_SERVER", False)

if CENTRAL_SERVER:
    ACCOUNT_ACTIVATION_DAYS = localor("ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = localor("DEFAULT_FROM_EMAIL", "kalite@adhocsync.com")
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central")
    EMAIL_BACKEND           = "postmark.backends.PostmarkBackend"
    AUTH_PROFILE_MODULE     = 'central.UserProfile'

if not CENTRAL_SERVER:
    MIDDLEWARE_CLASSES += (
        "securesync.middleware.DBCheck",
        "securesync.middleware.AuthFlags",
        "main.middleware.SessionLanguage",
    )
    TEMPLATE_CONTEXT_PROCESSORS += (
        "main.custom_context_processors.languages",
    )


# import these one extra time to overwrite any settings not explicitly looking for local settings
try:
    from local_settings import *
except ImportError:
    pass

syncing_models = []
def add_syncing_models(models):
    for model in models:
        if model not in syncing_models:
            syncing_models.append(model)

slug_key = {
    "Topic": "id",
    "Video": "readable_id",
    "Exercise": "name",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
}
