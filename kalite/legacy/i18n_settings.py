"""

benjaoming:

This file replaces i18n.settings temporarily until i18n.__init__.py has been
cleaned up to not contain references to django post-load modules.


DO NOT MODIFY THIS FILE UNLESS ABSOLUTELY NECESSARY


This will be cleaned up in KA Lite 0.14


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


# This is the standard method... but doesn't work because we cannot load
# kalite.i18n while loading settings because of its __init__.py
# from pkgutil import get_data
# I18N_DATA_PATH = get_data("kalite.i18n", "data")

# Use resource_filename instead of get_data because it does not try to open
# a file and does not complain that its a directory

from kalite.settings.base import USER_WRITABLE_LOCALE_DIR

from pkg_resources import resource_filename
I18N_DATA_PATH = resource_filename("kalite", "i18n/data")
LANG_LOOKUP_FILEPATH = os.path.join(I18N_DATA_PATH, "languagelookup.json")

__dubbed_video_mapping_source = os.path.join(I18N_DATA_PATH, "dubbed_video_mappings.json")
DUBBED_VIDEOS_MAPPING_FILEPATH = os.path.join(USER_WRITABLE_LOCALE_DIR, "dubbed_video_mappings.json")

# If user does not have this file in their own directory, create a new one as a
# copy of the distributed one since user processes may write to it
if os.path.isfile(__dubbed_video_mapping_source) and not os.path.isfile(DUBBED_VIDEOS_MAPPING_FILEPATH):
    open(DUBBED_VIDEOS_MAPPING_FILEPATH, "w").write(
        file(__dubbed_video_mapping_source, "r").read()
    )

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
