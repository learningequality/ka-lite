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
def get_dubbed_video_map(lang_code=None, force=False):
    global DUBBED_VIDEO_MAP, DUBBED_VIDEOS_MAPPING_FILE
    if DUBBED_VIDEO_MAP is None or force:
        if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILE):
            call_command("generate_dubbed_video_mappings")
        DUBBED_VIDEO_MAP = json.loads(open(DUBBED_VIDEOS_MAPPING_FILE).read())
    return DUBBED_VIDEO_MAP.get(lang_code, {}) if lang_code else DUBBED_VIDEO_MAP

YT2ID_MAP = None
def get_file2id_map(force=False):
    global YT2ID_MAP
    if YT2ID_MAP is None or force:
        YT2ID_MAP = {}
        for dic in get_dubbed_video_map().values():
            for english_youtube_id, dubbed_youtube_id in dic.iteritems():
                YT2ID_MAP[dubbed_youtube_id] = english_youtube_id
    return YT2ID_MAP

ID2OKLANG_MAP = None
def get_id2oklang_map(video_id, force=False):
    global ID2OKLANG_MAP
    if ID2OKLANG_MAP is None or force:
        ID2OKLANG_MAP = {}
        for lang, dic in get_dubbed_video_map().iteritems():
            for english_youtube_id, dubbed_youtube_id in dic.iteritems():
                cur_video_id = get_video_id(english_youtube_id)
                ID2OKLANG_MAP[cur_video_id] = ID2OKLANG_MAP.get(english_youtube_id, {})
                ID2OKLANG_MAP[cur_video_id][lang] = dubbed_youtube_id
    if video_id:
        # Not all IDs made it into the spreadsheet, so by default, use the video_id as the youtube_id
        return ID2OKLANG_MAP.get(video_id, {"english": get_youtube_id(video_id, None)})
    else:
        return ID2OKLANG_MAP

def get_youtube_id(video_id, lang_code=settings.LANGUAGE_CODE):
    if not lang_code:  # looking for the base/default youtube_id
        return video_id
    return get_dubbed_video_map().get(video_id, {}).get(lang_code)

def get_video_id(youtube_id):
    """
    Youtube ID is assumed to be the non-english version.
    """
    return get_file2id_map().get(youtube_id, youtube_id)

def get_srt_url(youtube_id, code):
    return settings.STATIC_URL + "subtitles/%s/%s.srt" % (code, youtube_id)

def get_srt_path_on_disk(youtube_id, code):
    return os.path.join(settings.STATIC_ROOT, "subtitles", code, youtube_id + ".srt")


lang_lookup_filename = "languagelookup.json"
lang_lookup_path = os.path.join(settings.DATA_PATH, lang_lookup_filename)
CODE2LANG_MAP = None
def get_code2lang_map(force=False):
    global lang_lookup_path, CODE2LANG_MAP
    if force or not CODE2LANG_MAP:
        CODE2LANG_MAP = json.loads(open(lang_lookup_path).read())
        # convert all upper to lower
        for entry in CODE2LANG_MAP.values():
            entry = dict(zip(entry.keys(), [v.lower() for v in entry.values()]))
    return CODE2LANG_MAP

LANG2CODE_MAP = None
def get_langcode_map(force=False):
    global lang_lookup_path, LANG2CODE_MAP
    if force or not LANG2CODE_MAP:
        LANG2CODE_MAP = {}
        for code, entries in get_code2lang_map(force=force).iteritems():
            for lang in entries.values():
                if lang:
                    LANG2CODE_MAP[lang.lower()] = code
    return LANG2CODE_MAP

def get_language_name(lang_code, native=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    global lang_lookup_path

    # Convert code if neccessary
    lang_code = convert_language_code_format(lang_code)

    language_entry = get_langcode_map().get(lang_code.lower())
    if not language_entry:
       raise Exception("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, lang_lookup_path))

    if not native:
        return language_entry["name"]
    else:
        return language_entry["native_name"]


def get_language_code(language):
    """Return ISO 639-1 language code full English or native language name from ; raise exception if it isn't hardcoded yet"""
    global lang_lookup_path

    lang_code = get_langcode_map().get(language.lower())
    if not lang_code:
       raise Exception("We don't have language '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (language, lang_lookup_path))
    return lang_code


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