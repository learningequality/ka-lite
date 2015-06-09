"""





DO NOT MODIFY THIS FILE OR LOAD THIS MODULE.


Because of i18n.__init__.py, we cannot load this module independently of its
own child module's preconditions.

I.e. i18n.__init__.py expects the django.conf.settings to have loaded, but
i18n.settings is a precondition for loading the project's settings module
kalite.settings

Nasty stuff.

Will be cleaned up in 0.14.



"""


import logging
import os

try:
    from kalite import local_settings
except ImportError:
    local_settings = object()


#######################
# Functions to support settings
#######################

def allow_all_languages_alist(langlookupfile):
    with open(langlookupfile) as f:
        import json
        langlookup = json.load(f)
    for lc, metadata in langlookup.iteritems():
        lc = (lc.
              lower().          # django only accepts lowercase languages
              replace('-', '_') # django needs the underscore
        )
        yield (lc, metadata['name'])


########################
# (Aron): Setting the LANGUAGES configuration.
########################

# JSON file of all languages and their names
I18N_DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
LANG_LOOKUP_FILEPATH = os.path.join(I18N_DATA_PATH, "languagelookup.json")

# Whether to turn on crowdin's in-context localization feature
IN_CONTEXT_LOCALIZED = getattr(local_settings, "IN_CONTEXT_LOCALIZED", False)

# This is a bit more involved, as we need to hand out to a function to calculate
#   the LANGUAGES settings. This LANGUAGES setting is basically a whitelist of
#   languages. Anything not in here is not accepted by Django, and will simply show
#   English instead of the selected language.
if getattr(local_settings, 'LANGUAGES', None):
    LANGUAGES = local_settings.LANGUAGES
else:
    try:
        LANGUAGES = set(allow_all_languages_alist(LANG_LOOKUP_FILEPATH))
    except Exception as e:
        logging.error("Error loading %s (%s); Django will use its own builtin LANGUAGES list." % (LANG_LOOKUP_FILEPATH, e))
