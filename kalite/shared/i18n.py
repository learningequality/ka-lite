"""
Utility functions for i18n related tasks on the distributed server
"""
import json
import re 
import os

import settings


def get_srt_url(video_id, code):
    return settings.STATIC_URL + "subtitles/%s/%s.srt" % (code, video_id)

def get_srt_path_on_disk(video_id, code):
    return os.path.join(settings.STATIC_ROOT, "subtitles", code, video_id + ".srt")

def get_language_name(lang_code, native=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    # Open lookup dictionary 
    lang_lookup_filename = "languagelookup.json"
    lang_lookup_path = os.path.join(settings.DATA_PATH, lang_lookup_filename)
    LANGUAGE_LOOKUP = json.loads(open(lang_lookup_path).read())

    # Convert code if neccessary 
    lang_code = convert_language_code_format(lang_code)

    language_entry = LANGUAGE_LOOKUP.get(lang_code)    
    if not language_entry:
       raise Exception("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, lang_lookup_path))

    if not native:
        language_name = language_entry["name"]
    else:
        language_name = language_entry["native_name"]

    return language_name


def convert_language_code_format(lang_code, for_crowdin=False):
    """
    Return language code for lookup in local dictionary. 

    Note: For language codes with localizations, Django requires the format xx_XX (e.g. Spanish from Spain = es_ES)  
    not: xx-xx, xx-XX, xx_xx.
    """
    lang_code = lang_code.lower()
    code_parts = re.split('-|_', lang_code)    
    if len(code_parts) >  1:
        assert len(code_parts) == 2
        code_parts[1] = code_parts[1].upper()
        if not for_crowdin:
            lang_code = "_".join(code_parts)
        else:
            lang_code = "-".join(code_parts)

    return lang_code


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


def get_installed_subtitles(video_id):
    """
    Returns a list of all language codes that contain subtitles for this video.
    """

    installed_subtitles = []

    # Loop through locale folders
    for locale_dir in settings.LOCALE_PATHS:
        if not os.path.exists(locale_dir):
            continue

        installed_subtitles += [lang for lang in os.listdir(locale_dir) if os.path.exists(get_srt_path_on_disk(video_id, lang))]

    return sorted(installed_subtitles)
