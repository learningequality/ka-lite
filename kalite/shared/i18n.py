"""
Utility functions for i18n related tasks on the distributed server
"""
import json
import os
import re 

from django.core.management import call_command
from django.http import HttpRequest
from django.views.i18n import javascript_catalog

import settings
from utils.general import ensure_dir

DUBBED_VIDEOS_MAPPING_FILE = os.path.join(settings.STATIC_ROOT, "data", "i18n", "dubbed_video_mappings.json")


DUBBED_VIDEO_MAP = None
def get_dubbed_video_map(force=False):
    global DUBBED_VIDEO_MAP, DUBBED_VIDEOS_MAPPING_FILE
    if DUBBED_VIDEO_MAP is None or force:
        if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILE):
            call_command("generate_dubbed_video_mappings")
        lang2vid = json.loads(open(DUBBED_VIDEOS_MAPPING_FILE).read())

        DUBBED_VIDEO_MAP = {}
        for dic in lang2vid.values():
            for english_youtube_id, dubbed_youtube_id in dic.iteritems():
                DUBBED_VIDEO_MAP[dubbed_youtube_id] = english_youtube_id
    return DUBBED_VIDEO_MAP

def get_video_id(youtube_id):
    """
    Youtube ID is assumed to be the non-english version.
    """
    return get_dubbed_video_map().get(youtube_id, youtube_id)

def get_srt_url(youtube_id, code):
    return settings.STATIC_URL + "subtitles/%s/%s.srt" % (code, youtube_id)

def get_srt_path_on_disk(youtube_id, code):
    return os.path.join(settings.STATIC_ROOT, "subtitles", code, youtube_id + ".srt")

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


def get_installed_subtitles(youtube_id):
    """
    Returns a list of all language codes that contain subtitles for this video.
    """

    installed_subtitles = []

    # Loop through locale folders
    for locale_dir in settings.LOCALE_PATHS:
        if not os.path.exists(locale_dir):
            continue

        installed_subtitles += [lang for lang in os.listdir(locale_dir) if os.path.exists(get_srt_path_on_disk(youtube_id, lang))]

    return sorted(installed_subtitles)


def update_jsi18n_file(code="en"):
    """
    For efficieny's sake, we want to cache Django's
    js18n file.  So, generate that file here, then
    save to disk--it won't change until the next language pack update!
    """
    output_dir = os.path.join(settings.STATIC_ROOT, "js", "i18n")
    ensure_dir(output_dir)
    output_file = os.path.join(output_dir, "%s.js" % code)

    request = HttpRequest()
    request.path = output_file
    request.session = {'django_language': code}

    response = javascript_catalog(request, packages=('ka-lite.locale',))
    with open(output_file, "w") as fp:
        fp.write(response.content)