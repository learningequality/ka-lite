import json
import os

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

DEBUG = hasattr(local_settings, "DEBUG") and local_settings.DEBUG or False
TEMPLATE_DEBUG = hasattr(local_settings, "TEMPLATE_DEBUG") and local_settings.TEMPLATE_DEBUG or DEBUG

ADMINS = (
    ("Jamie Alexandre", "jamalex@gmail.com"),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": "userdata.sqlite",              # Or path to database file if using sqlite3.
    }
}

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

DATA_PATH = PROJECT_PATH + "/static/data/"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = "America/Los_Angeles"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = hasattr(local_settings, "LANGUAGE_CODE") and local_settings.LANGUAGE_CODE or "en-us"

# SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
ADMIN_MEDIA_PREFIX = "/static/admin/"

# Directory where static files will be consolidated
if DEBUG:
    STATIC_ROOT = PROJECT_PATH + "/static-files/"
else:
    STATIC_ROOT = PROJECT_PATH + "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    PROJECT_PATH + "/static/",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = hasattr(local_settings, "SECRET_KEY") and local_settings.SECRET_KEY \
    or "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u"

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
#     "django.template.loaders.eggs.Loader",
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "securesync.middleware.AuthFlags",
)

ROOT_URLCONF = "kalite.urls"

TEMPLATE_DIRS = (PROJECT_PATH + "/templates",)

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django_extensions",
    "south",
    "main",
    "central",
    "securesync",
    "django.contrib.humanize",
    "django.contrib.messages",
    "chronograph",
    "config",
)

CENTRAL_SERVER_HOST = "http://127.0.0.1:9000/"

CENTRAL_SERVER = hasattr(local_settings, "CENTRAL_SERVER") and local_settings.CENTRAL_SERVER or False

if CENTRAL_SERVER:
    ACCOUNT_ACTIVATION_DAYS = 7
    DEFAULT_FROM_EMAIL = "kalite@adhocsync.com"
    INSTALLED_APPS += ("postmark", "kalite.registration", "central")
    EMAIL_BACKEND = "postmark.backends.PostmarkBackend"
    AUTH_PROFILE_MODULE = 'central.UserProfile'

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
