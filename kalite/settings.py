import json
import os
import logging


def get_local_or_not( name, value ):
    """Get """
    
    return get_or_set_from_db(name=name, value=value, cursor=None, dtype=None, comment=None)


def get_or_set_from_db(cursor, name, value, dtype=None, comment=None):
    """Gets the settings from the localsettings, database, or 
       pushes them to the database and uses the value provided. """
    
    # Default: returned value is the same as that passed in
    set_value = value
    
    # First check from globals
    if name in globals():
        logging.debug('[0]: found value for %s in globals'%name)
        set_value = globals()[name]
    
    # Second, check from local settings
    #elif name in globals()['local_settings']:       
    #    logging.debug('[1]: found value for %s in local settings'%name)
    
    # Now we need to go to the database
    elif cursor:
        db_value = cursor.execute("SELECT value FROM config_settings WHERE Name='%s'"%(name)).fetchall()
        
        # Third: get it from the database
        if len(db_value)==1:
            logging.debug('[1]: found the value for %s in the database.'%(name))
            set_value = db_value[0][0]
            
        # Fourth: push it to the database, and use the provided value
        else:
            logging.debug('[2]: had to insert the value for %s into the database.'%(name))
            cursor.execute("INSERT INTO config_settings(Name,Value,DataType) values(?,?,?)",(name,value,dtype))
    
    else:
        logging.debug('[3]: using passed in value')
        
    return set_value
    
##########


# Local settings will be put into the "global" space
#   within this file :)
try:
    from local_settings import *
    import local_settings
except ImportError:
    local_settings = {}
    
    
# Static settings, required for setting dynamic settings
PROJECT_PATH = get_local_or_not("PROJECT_PATH", os.path.dirname(os.path.realpath(__file__)))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": get_local_or_not("DATABASE_PATH", PROJECT_PATH + "/database/data.sqlite"),
        "OPTIONS": {
            "timeout": 60,
        },
    }
}


# Dynamic settings, configurable in the db
# 
# First we validate that they're there.  If not, we add them with defaults.
    #(cursor.execute('SELECT * FROM settings')
try:
    import sqlite3
    conn = sqlite3.connect(DATABASES["default"]["NAME"])
    cursor = conn.cursor()
except Exception as e:
    logging.warn("Failed to connect to database (%s);\nwill read default settings from settings.py"%e)
    cursor = None

# Debug stuff
DEBUG          = get_or_set_from_db(cursor, 'DEBUG',          0, 'INTEGER', "Print out debug errors/info to website?")

# Set up logging
logging.getLogger().setLevel(logging.DEBUG*DEBUG + logging.INFO*(1-DEBUG))

TEMPLATE_DEBUG = get_or_set_from_db(cursor, 'TEMPLATE_DEBUG', 0, 'INTEGER', "Print out template debug errors/info to website?")

# Paths & urls
DATA_PATH      = get_or_set_from_db(cursor, 'DATA_PATH', os.path.realpath(PROJECT_PATH + "/static/data/")+"/", 'TEXT', "Local file path to exercises")
CONTENT_ROOT   = get_or_set_from_db(cursor, 'CONTENT_ROOT', os.path.realpath(PROJECT_PATH + "/../content/")+"/", 'TEXT', "Local file path to videos")
CONTENT_URL    = get_or_set_from_db(cursor, 'CONTENT_URL', "/content/", 'TEXT', "URL endpoint to videos")
MEDIA_ROOT     = get_or_set_from_db(cursor, 'MEDIA_ROOT', os.path.realpath(PROJECT_PATH + "/static/")+"/", 'TEXT', "?")
MEDIA_URL      = get_or_set_from_db(cursor, 'MEDIA_URL', "/static/", 'TEXT', "?")
STATIC_URL     = get_or_set_from_db(cursor, 'STATIC_URL', "/static/", 'TEXT', "?")
TEMPLATE_DIRS  = (get_or_set_from_db(cursor, 'TEMPLATE_DIRS', os.path.realpath(PROJECT_PATH + "/templates"), 'TEXT', "?"))

# Server & API stuff
CENTRAL_SERVER_HOST = get_or_set_from_db(cursor, 'CENTRAL_SERVER_HOST', "https://kalite.adhocsync.com/", 'TEXT', "?")
INTERNAL_IPS   = (get_or_set_from_db(cursor, 'INTERNAL_IPS',   "127.0.0.1", 'TEXT', ""))


# Internationalization
TIME_ZONE      = get_or_set_from_db(cursor, 'TIME_ZONE', "America/Los_Angeles", 'TEXT', "Local time zone for this installation. Choices can be found here: http://en.wikipedia.org/wiki/List_of_tz_zones_by_name")
LANGUAGE_CODE  = get_or_set_from_db(cursor, 'LANGUAGE_CODE', 'en-us', 'TEXT', "Language code for this installation. All choices can be found here: http://www.i18nguy.com/unicode/language-identifiers.html")
USE_I18N       = get_or_set_from_db(cursor, 'USE_I18N', 1, 'INTEGER', "If you set this to False, Django will make some optimizations so as not to load the internationalization machinery.")
USE_L10N       = get_or_set_from_db(cursor, 'USE_L10N', 1, 'INTEGER', "If you set this to False, Django will not format dates, numbers and calendars according to the current locale")

try:
    if conn:
        conn.commit()
except Exception as e:
    logging.warn("Failed to push settings to the database: %s"%e)



# Other static settings that are not going through the database
#

#
# Ones that can deal with local_settings
CENTRAL_SERVER = get_local_or_not("CENTRAL_SERVER", False)


# Make this unique, and don't share it with anybody.
SECRET_KEY = get_local_or_not("SECRET_KEY", "8qq-!fa$92i=s1gjjitd&%s@4%ka9lj+=@n7a&fzjpwu%3kd#u")

# Ones that are not set up for local_settings.py
#
LOCALE_PATHS = (os.path.realpath(PROJECT_PATH + "/../locale"),)

ADMINS = (
    ("Jamie Alexandre", "jamalex@gmail.com"),
)

MANAGERS = ADMINS

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
)

if DEBUG or CENTRAL_SERVER:
    INSTALLED_APPS += ("django_extensions",)

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
