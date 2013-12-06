"""
Utility functions for i18n related tasks on the distributed server
"""
import json
import os
import re
import requests

from django.http import HttpRequest
from django.views.i18n import javascript_catalog

import settings
import version
from utils.general import ensure_dir


if settings.CENTRAL_SERVER:
    AMARA_HEADERS = {
        "X-api-username": settings.AMARA_USERNAME,
        "X-apikey": settings.AMARA_API_KEY,
    }

SUBTITLES_DATA_ROOT = os.path.join(settings.DATA_PATH_SECURE, "subtitles")
LANGUAGE_PACK_ROOT = os.path.join(settings.MEDIA_ROOT, "language_packs")

LANGUAGE_SRT_SUFFIX = "_download_status.json"
SRTS_JSON_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "srts_remote_availability.json")
DUBBED_VIDEOS_MAPPING_FILEPATH = os.path.join(settings.DATA_PATH_SECURE, "i18n", "dubbed_video_mappings.json")
LANGUAGE_PACK_AVAILABILITY_FILEPATH = os.path.join(LANGUAGE_PACK_ROOT, "language_pack_availability.json")
SUBTITLE_COUNTS_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "subtitle_counts.json")
LANG_LOOKUP_FILEPATH = os.path.join(settings.DATA_PATH_SECURE, "i18n", "languagelookup.json")

LOCALE_ROOT = settings.LOCALE_PATHS[0]

def get_language_pack_metadata_filepath(lang_code):
    lang_code = lcode_to_django_dir(lang_code)
    return os.path.join(LOCALE_ROOT, lang_code, "%s_metadata.json" % lang_code)

def get_language_pack_filepath(lang_code, version=version.VERSION):
    return os.path.join(LANGUAGE_PACK_ROOT, version, "%s.zip" % lcode_to_ietf(lang_code))

def get_language_pack_url(lang_code, version=version.VERSION):
    return "http://%s/%s" % (
        settings.CENTRAL_SERVER_HOST,
        get_language_pack_filepath(lang_code, version=version)[len(settings.PROJECT_PATH):],
    )

class LanguageNotFoundError(Exception):
    pass

DUBBED_VIDEO_MAP = None
def get_dubbed_video_map(lang_code=None, force=False):
    global DUBBED_VIDEO_MAP, DUBBED_VIDEOS_MAPPING_FILEPATH
    if DUBBED_VIDEO_MAP is None or force:
        try:
            if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH):
                if settings.CENTRAL_SERVER:
                    call_command("generate_dubbed_video_mappings")
                else:
                    response = requests.get("http://%s/api/i18n/videos/dubbed_video_map" % (settings.CENTRAL_SERVER_HOST))
                    response.raise_for_status()
                    with open(DUBBED_VIDEOS_MAPPING_FILEPATH, "wb") as fp:
                        fp.write(response.content)  # wait until content has been confirmed before opening file.
            with open(DUBBED_VIDEOS_MAPPING_FILEPATH, "r") as fp:
                DUBBED_VIDEO_MAP = json.load(fp)
        except:
            DUBBED_VIDEO_MAP = {}  # setting this will avoid triggering reload on every call
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


CODE2LANG_MAP = None
def get_code2lang_map(force=False):
    global LANG_LOOKUP_FILEPATH, CODE2LANG_MAP
    if force or not CODE2LANG_MAP:
        with open(LANG_LOOKUP_FILEPATH, "r") as fp:
            lmap = json.load(fp)
        CODE2LANG_MAP = {}
        # convert all upper to lower
        for lang_code, entry in lmap.iteritems():
            CODE2LANG_MAP[lcode_to_ietf(lang_code)] = dict(zip(entry.keys(), [v.lower() for v in entry.values()]))
    return CODE2LANG_MAP

LANG2CODE_MAP = None
def get_langcode_map(force=False):
    global LANG_LOOKUP_FILEPATH, LANG2CODE_MAP
    if force or not LANG2CODE_MAP:
        LANG2CODE_MAP = {}
        for code, entries in get_code2lang_map(force=force).iteritems():
            for lang in entries.values():
                if lang:
                    LANG2CODE_MAP[lang.lower()] = lcode_to_ietf(code)
    return LANG2CODE_MAP

def get_language_name(lang_code, native=False, error_on_missing=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    global LANG_LOOKUP_FILEPATH

    # Convert code if neccessary
    lang_code = lcode_to_ietf(lang_code)

    language_entry = get_code2lang_map().get(lang_code)
    if not language_entry:
        if error_on_missing:
            raise LanguageNotFoundError("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, LANG_LOOKUP_FILEPATH))
        else:
            # Fake it
            language_entry = {"name": lang_code, "native_name": lang_code}

    if not native:
        return language_entry["name"]
    else:
        return language_entry["native_name"]


def get_language_code(language, for_django=False):
    """Return ISO 639-1 language code full English or native language name from ; raise exception if it isn't hardcoded yet"""
    global LANG_LOOKUP_FILEPATH

    lang_code = get_langcode_map().get(language.lower())
    if not lang_code:
       raise LanguageNotFoundError("We don't have language '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (language, LANG_LOOKUP_FILEPATH))
    elif for_django:
        return lcode_to_django_dir(lang_code)
    else:
        return lang_code


def lcode_to_django_lang(lang_code):
    return lcode_to_ietf(lang_code).lower()

def lcode_to_django_dir(lang_code):
    return convert_language_code_format(lang_code, for_django=True)

def lcode_to_ietf(lang_code):
    return convert_language_code_format(lang_code, for_django=False)


def convert_language_code_format(lang_code, for_django=True):
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
        if for_django:
            lang_code = "_".join(code_parts)
        else:
            lang_code = "-".join(code_parts)

    return lang_code

def get_lang_map_filepath(lang_code):
    return os.path.join(SUBTITLES_DATA_ROOT, "languages", lang_code + LANGUAGE_SRT_SUFFIX)


def get_languages_on_disk():
    """
    On-disk method to show currently installed languages and meta data.
    """
    raise Exception("NYI; this needs to validate that all the parts are in the right places (mo and srt), and should be moved into a languagepackscan command--the only place it's relevant.")
    installed_languages = []

    # Loop through locale folders
    for locale_dir in settings.LOCALE_PATHS:
        if not os.path.exists(locale_dir):
            continue

        # Loop through folders in each locale dir
        for lang in os.listdir(locale_dir):
            # Inside each folder, read from the JSON file - language name, % UI trans, version number
            try:
                with open(os.path.join(locale_dir, lang, "%s_metadata.json" % lang), "r") as fp:
                    lang_meta = json.load(fp)
            except:
                lang_meta = {}
            lang = lang_meta
            installed_languages.append(lang)

    # return installed_languages
    return installed_languages


def get_subtitles_on_disk(youtube_id):
    """
    Returns a list of all language codes that contain subtitles for this video.

    Central and distributed servers store in different places, so loop differently
    """

    def on_disk_central(youtube_id):
        installed_subtitles = []

        # Loop through locale folders
        for locale_dir in settings.LOCALE_PATHS:
            if not os.path.exists(locale_dir):
                continue
            installed_subtitles += [lang for lang in os.listdir(locale_dir) if os.path.exists(get_srt_path_on_disk(youtube_id, lang))]
        return installed_subtitles

    def on_disk_distributed(youtube_id):
        subtitles_root = os.path.join(settings.STATIC_ROOT, "subtitles")
        if not os.path.exists(subtitles_root):
            return []
        else:
            return [lang for lang in os.listdir(subtitles_root) if os.path.exists(get_srt_path_on_disk(youtube_id, lang))]

    return sorted(on_disk_central(youtube_id) if settings.CENTRAL_SERVER else on_disk_distributed(youtube_id))


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
