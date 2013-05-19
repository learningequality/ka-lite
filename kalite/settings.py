import json
import os
import logging

try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}

def local_or_(setting_name, default_val):
    """Returns local_settings version if it exists (and is non-empty), otherwise uses default value"""
    return hasattr(local_settings, setting_name) and getattr(local_settings, setting_name) or default_val
    
DEBUG          = local_or_("DEBUG", False)
TEMPLATE_DEBUG = local_or_("TEMPLATE_DEBUG", False)

# Set logging level based on the value of DEBUG (evaluates to 0 if False, 1 if True)
logging.getLogger().setLevel(logging.DEBUG*DEBUG + logging.INFO*(1-DEBUG))
    
INTERNAL_IPS   = local_or_("INTERNAL_IPS", ("127.0.0.1",))

CENTRAL_SERVER = local_or_("CENTRAL_SERVER", False)

# info about the central server(s)
SECURESYNC_PROTOCOL   = local_or_("SECURESYNC_PROTOCOL",   "https")
CENTRAL_SERVER_DOMAIN = local_or_("CENTRAL_SERVER_DOMAIN", "adhocsync.com")
CENTRAL_SERVER_HOST   = local_or_("CENTRAL_SERVER_HOST",   "kalite.%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_FROM_EMAIL    = local_or_("CENTRAL_FROM_EMAIL",    "kalite@%s"%CENTRAL_SERVER_DOMAIN)
CENTRAL_ADMIN_EMAIL   = local_or_("CENTRAL_ADMIN_EMAIL",   "info@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN
CENTRAL_CONTACT_EMAIL = local_or_("CENTRAL_CONTACT_EMAIL", "info@learningequality.org")#"kalite@%s"%CENTRAL_SERVER_DOMAIN
CENTRAL_WIKI_URL      = local_or_("CENTRAL_WIKI_URL",      "http://kalitewiki.learningequality.org/")#http://%kalitewiki.s/%CENTRAL_SERVER_DOMAIN   

ADMINS         = local_or_("ADMINS", ( ("KA Lite Team", CENTRAL_ADMIN_EMAIL), ) )

MANAGERS       = local_or_("MANAGERS", ADMINS)

PROJECT_PATH   = local_or_("PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))

LOCALE_PATHS   = local_or_("LOCALE_PATHS", (PROJECT_PATH + "/../locale",))

DATABASES      = local_or_("DATABASES", {
    "default": {
        "ENGINE": local_or_("DATABASE_TYPE", "django.db.backends.sqlite3"),
        "NAME"  : local_or_("DATABASE_PATH", PROJECT_PATH + "/database/data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
})

DATA_PATH      = local_or_("DATA_PATH", PROJECT_PATH + "/static/data/")

CONTENT_ROOT   = local_or_("CONTENT_ROOT", PROJECT_PATH + "/../content/")
CONTENT_URL    = local_or_("CONTENT_URL", "/content/")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE      = local_or_("TIME_ZONE", "America/Los_Angeles")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE  = local_or_("LANGUAGE_CODE", "en-us")

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N       = local_or_("USE_I18N", True)

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N       = local_or_("USE_L10N", False)

MEDIA_URL       = local_or_("MEDIA_URL", "/media/")
MEDIA_ROOT      = local_or_("MEDIA_ROOT", PROJECT_PATH + "/media/") # not currently used
STATIC_URL      = local_or_("STATIC_URL", "/static/")
if DEBUG: # jedi mind-trick on django to serve up static files in debug/release,
          #   while still following the semantics of django STATIC_ROOT/STATIC_URL
    STATIC_ROOT      = "" # this should point to a directory where we can collect and shove all files.
                          #    since we have no intention of doing so, set it to None.
    STATICFILES_DIRS = ( local_or_("STATIC_ROOT", PROJECT_PATH + "/static/"), )
else:
    STATIC_ROOT     = local_or_("STATIC_ROOT", PROJECT_PATH + "/static/")
    
 
 # Make this unique, and don't share it with anybody.
SECRET_KEY     = local_or_("SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

TEMPLATE_DIRS  = local_or_("TEMPLATE_DIRS", (PROJECT_PATH + "/templates",))


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
    "django.contrib.staticfiles",
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
    ACCOUNT_ACTIVATION_DAYS = local_or_("ACCOUNT_ACTIVATION_DAYS", 7)
    DEFAULT_FROM_EMAIL      = local_or_("DEFAULT_FROM_EMAIL", CENTRAL_FROM_EMAIL)
    INSTALLED_APPS         += ("postmark", "kalite.registration", "central")
    EMAIL_BACKEND           = local_or_("EMAIL_BACKEND", "postmark.backends.PostmarkBackend")
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
