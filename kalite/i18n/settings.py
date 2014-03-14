import glob
import json
import logging
import os

try:
    import local_settings
except ImportError:
    local_settings = object()


#######################
# Functions to support settings
#######################

def allow_all_languages_alist(langlookupfile):
    with open(langlookupfile) as f:
        langlookup = json.load(f)
    for lc, metadata in langlookup.iteritems():
        lc = (lc.
              lower().          # django only accepts lowercase languages
              replace('-', '_') # django needs the underscore
        )
        yield (lc, metadata['name'])

def allow_languages_in_locale_path_alist(localepaths):
    for localepath in localepaths:
        langdirs = os.listdir(localepath) if os.path.exists(localepath) else []
        for langdir in langdirs:
            try:
                mdfiles = glob.glob(os.path.join(localepath, langdir, '*_metadata.json'))
                for mdfile in mdfiles:
                    with open(mdfile) as f:
                        metadata = json.load(f)
                    lc = metadata['code'].lower() # django reads language codes in lowercase
                    yield (lc, metadata['name'])
                    break
            except Exception as e:
                logging.error("Error loading %s metadata: %s" % (langdir, e))



########################
# (Aron): Setting the LANGUAGES configuration.
########################

# JSON file of all languages and their names
LANG_LOOKUP_FILEPATH = os.path.join(DATA_PATH, "i18n", "languagelookup.json")

# This is a bit more involved, as we need to hand out to a function to calculate
#   the LANGUAGES settings. This LANGUAGES setting is basically a whitelist of
#   languages. Anything not in here is not accepted by Django, and will simply show
#   English instead of the selected language.
if getattr(local_settings, 'LANGUAGES', None):
    LANGUAGES = local_settings.LANGUAGES
else:
    try:
        LANGUAGES = set(allow_all_languages_alist(LANG_LOOKUP_FILEPATH))
    except Exception:
        logging.error("%s not found. Django will use its own builtin LANGUAGES list." % LANG_LOOKUP_FILEPATH)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.i18n",
    "i18n.custom_context_processors.languages",
)

MIDDLEWARE_CLASSES = (
    "kalite.i18n.middleware.SessionLanguage",
    'django.middleware.locale.LocaleMiddleware',  # Must define after i18n.middleware.SessionLanguage
)
