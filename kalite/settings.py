import json
import os
import sys
import tempfile

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

DEBUG = hasattr(local_settings, "DEBUG") and local_settings.DEBUG or False
TEMPLATE_DEBUG = hasattr(local_settings, "TEMPLATE_DEBUG") and local_settings.TEMPLATE_DEBUG or DEBUG

INTERNAL_IPS = ("127.0.0.1",)

CENTRAL_SERVER = hasattr(local_settings, "CENTRAL_SERVER") and local_settings.CENTRAL_SERVER or False

ADMINS = (
    ("Jamie Alexandre", "jamalex@gmail.com"),
)

MANAGERS = ADMINS

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

LOCALE_PATHS = (PROJECT_PATH + "/../locale",)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": PROJECT_PATH + "/database/data.sqlite",
        "OPTIONS": {
            "timeout": 60,
        },
    }
}

DATA_PATH = PROJECT_PATH + "/static/data/"

CONTENT_ROOT = PROJECT_PATH + "/../content/"
CONTENT_URL = "/content/"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = "America/Los_Angeles"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = hasattr(local_settings, "LANGUAGE_CODE") and local_settings.LANGUAGE_CODE or "en-us"

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = False

MEDIA_ROOT = PROJECT_PATH + "/static/"
MEDIA_URL = "/static/"

STATIC_URL = "/dummy/" # not used

# Make this unique, and don't share it with anybody.
SECRET_KEY = hasattr(local_settings, "SECRET_KEY") and local_settings.SECRET_KEY \
    or "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u"

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
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.GetNextParam",
    "django.middleware.csrf.CsrfViewMiddleware",
)
if DEBUG:
    MIDDLEWARE_CLASSES += (
        'django_snippets.profiling_middleware.ProfileMiddleware', # add ?prof to URL, to see performance stats
    )

ROOT_URLCONF = "kalite.urls"

TEMPLATE_DIRS = (PROJECT_PATH + "/templates",)

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
)

if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_extensions",)

CENTRAL_SERVER_HOST = "https://kalite.adhocsync.com/"

CENTRAL_SERVER = hasattr(local_settings, "CENTRAL_SERVER") and local_settings.CENTRAL_SERVER or False

if CENTRAL_SERVER:
    ACCOUNT_ACTIVATION_DAYS = 7
    DEFAULT_FROM_EMAIL = "kalite@adhocsync.com"
    INSTALLED_APPS += ("postmark", "kalite.registration", "central")
    EMAIL_BACKEND = "postmark.backends.PostmarkBackend"
    AUTH_PROFILE_MODULE = 'central.UserProfile'

if not CENTRAL_SERVER:
    MIDDLEWARE_CLASSES += (
        "securesync.middleware.DBCheck",
        "securesync.middleware.AuthFlags",
        "main.middleware.SessionLanguage",
    )
    TEMPLATE_CONTEXT_PROCESSORS += (
        "main.custom_context_processors.languages",
    )



# by default, cache for maximum possible
#   note: caching for 1000 years was too large a value
#   sys.maxint also can be too large (causes ValueError)
#   
#   but the combination is golden, of course! :D

CACHE_TIME = getattr(local_settings, "CACHE_TIME", min(60*60*24*365*1000, sys.maxint)) 

# Cache is activated in every case, 
#   EXCEPT: if CACHE_TIME=0
if CACHE_TIME or CACHE_TIME is None: # None can mean infinite caching to some functions
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': getattr(local_settings, "CACHE_LOCATION", tempfile.gettempdir()), # this is kind of OS-specific, so dangerous.
            'TIMEOUT': CACHE_TIME, # should be consistent
            'OPTIONS': {
                'MAX_ENTRIES': getattr(local_settings, "CACHE_MAX_ENTRIES", 5*2000) #2000 entries=~10,000 files
            },
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

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
