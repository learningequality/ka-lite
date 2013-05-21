import json
import os
import logging

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

DEBUG          = getattr(local_settings, "DEBUG", False)
TEMPLATE_DEBUG = getattr(local_settings, "TEMPLATE_DEBUG", DEBUG)

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
logging.getLogger().setLevel(logging.DEBUG*DEBUG + logging.INFO*(1-DEBUG))
    
INTERNAL_IPS   = getattr(local_settings, "INTERNAL_IPS", ("127.0.0.1",))

CENTRAL_SERVER = getattr(local_settings, "CENTRAL_SERVER", False)

# info about the central server(s)
SECURESYNC_PROTOCOL   = getattr(local_settings, "SECURESYNC_PROTOCOL",   "https")
CENTRAL_SERVER_DOMAIN = getattr(local_settings, "CENTRAL_SERVER_DOMAIN", "adhocsync.com")
CENTRAL_SERVER_HOST   = getattr(local_settings, "CENTRAL_SERVER_HOST",   "kalite.%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_WIKI_URL      = getattr(local_settings, "CENTRAL_WIKI_URL",      "http://kalitewiki.learningequality.org/")#http://%kalitewiki.s/%CENTRAL_SERVER_DOMAIN   
CENTRAL_FROM_EMAIL    = getattr(local_settings, "CENTRAL_FROM_EMAIL",    "kalite@%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_CONTACT_EMAIL = getattr(local_settings, "CENTRAL_CONTACT_EMAIL", "info@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN
CENTRAL_ADMIN_EMAIL   = getattr(local_settings, "CENTRAL_ADMIN_EMAIL",   "errors@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN

ADMINS         = getattr(local_settings, "ADMINS", ( ("KA Lite Team", CENTRAL_ADMIN_EMAIL), ) )

MANAGERS       = getattr(local_settings, "MANAGERS", ADMINS)

PROJECT_PATH   = getattr(local_settings, "PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))

LOCALE_PATHS   = getattr(local_settings, "LOCALE_PATHS", (PROJECT_PATH + "/../locale",))

DATABASES      = getattr(local_settings, "DATABASES", {
    "default": {
        "ENGINE": getattr(local_settings, "DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME"  : getattr(local_settings, "DATABASE_PATH", PROJECT_PATH + "/database/data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

DATA_PATH      = getattr(local_settings, "DATA_PATH", PROJECT_PATH + "/static/data/")

CONTENT_ROOT   = getattr(local_settings, "CONTENT_ROOT", PROJECT_PATH + "/../content/")
CONTENT_URL    = getattr(local_settings, "CONTENT_URL", "/content/")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = getattr(local_settings, "TIME_ZONE", "America/Los_Angeles")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = getattr(local_settings, "LANGUAGE_CODE", "en-us")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = getattr(local_settings, "USE_I18N", True)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N       = getattr(local_settings, "USE_L10N", False)

MEDIA_ROOT     = getattr(local_settings, "MEDIA_ROOT", PROJECT_PATH + "/static/")
MEDIA_URL      = getattr(local_settings, "MEDIA_URL", "/static/")
STATIC_URL     = getattr(local_settings, "STATIC_URL", "/static/")

# Make this unique, and don't share it with anybody.
SECRET_KEY     = getattr(local_settings, "SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

TEMPLATE_DIRS  = getattr(local_settings, "TEMPLATE_DIRS", (PROJECT_PATH + "/templates",))


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


if CENTRAL_SERVER:
    ACCOUNT_ACTIVATION_DAYS = getattr(local_settings, "ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = getattr(local_settings, "DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central")
    EMAIL_BACKEND           = getattr(local_settings, "EMAIL_BACKEND", "postmark.backends.PostmarkBackend")
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
