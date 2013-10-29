"""
Utility functions for i18n related tasks on the distributed server
"""
import os
import json

from django.utils.translation import ugettext as _

import settings


def get_installed_languages():
    """Return dictionary of currently installed languages and meta data"""

    installed_languages = []

    # Loop through locale folders
    for locale_dir in settings.LOCALE_PATHS:
        if not os.path.exists(locale_dir):
            continue

        # Loop through folders in each locale dir
        for lang in os.listdir(locale_dir):
            # Inside each folder, read from the JSON file - language name, % UI trans, version number
            try:
                lang_meta = json.loads(open(os.path.join(locale_dir, lang, "%s_metadata.json" % lang)).read())
            except:
                lang_meta = {}
            lang = lang_meta
            installed_languages.append(lang)

    # return installed_languages
    return installed_languages