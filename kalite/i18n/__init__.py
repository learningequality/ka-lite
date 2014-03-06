"""
Utility functions for i18n related tasks on the distributed server
"""
import bisect
import glob
import json
import os
import re
import requests
import shutil
from collections import OrderedDict, defaultdict

from django.core.management import call_command
from django.http import HttpRequest
from django.utils import translation
from django.views.i18n import javascript_catalog

################################################
###                                          ###
###   NOTE TO US:                            ###
###   main migrations import this file, so   ###
###   we CANNOT import main.models in here.  ###
###                                          ###
################################################
import settings
from settings import LANG_LOOKUP_FILEPATH
from settings import LOG as logging
from utils.general import ensure_dir, softload_json
from version import VERSION

CACHE_VARS = []


if settings.CENTRAL_SERVER:
    AMARA_HEADERS = {
        "X-api-username": settings.AMARA_USERNAME,
        "X-apikey": settings.AMARA_API_KEY,
    }

SUBTITLES_DATA_ROOT = os.path.join(settings.DATA_PATH, "subtitles")
LANGUAGE_PACK_ROOT = os.path.join(settings.MEDIA_ROOT, "language_packs")

LANGUAGE_SRT_SUFFIX = "_download_status.json"
SRTS_JSON_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "srts_remote_availability.json")
DUBBED_VIDEOS_MAPPING_FILEPATH = os.path.join(settings.DATA_PATH, "i18n", "dubbed_video_mappings.json")
SUBTITLE_COUNTS_FILEPATH = os.path.join(SUBTITLES_DATA_ROOT, "subtitle_counts.json")
SUPPORTED_LANGUAGES_FILEPATH = os.path.join(settings.DATA_PATH, "i18n", "supported_languages.json")
CROWDIN_CACHE_DIR = os.path.join(settings.PROJECT_PATH, "..", "_crowdin_cache")
LANGUAGE_PACK_BUILD_DIR = os.path.join(settings.DATA_PATH, "i18n", "build")

LOCALE_ROOT = settings.LOCALE_PATHS[0]

def get_lang_map_filepath(lang_code):
    return os.path.join(SUBTITLES_DATA_ROOT, "languages", lang_code + LANGUAGE_SRT_SUFFIX)

def get_language_pack_availability_filepath(version=VERSION):
    return os.path.join(LANGUAGE_PACK_ROOT, version, "language_pack_availability.json")

def get_localized_exercise_dirpath(lang_code, is_central_server=settings.CENTRAL_SERVER):
    ka_lang_code = lang_code.lower()

    if is_central_server:
        return os.path.join(get_lp_build_dir(ka_lang_code), "exercises")
    else:
        return os.path.join(settings.STATIC_ROOT, "js", "khan-exercises", "exercises", ka_lang_code)

def get_lp_build_dir(lang_code=None, version=None):
    global LANGUAGE_PACK_BUILD_DIR
    build_dir = LANGUAGE_PACK_BUILD_DIR
    if lang_code:
        build_dir = os.path.join(build_dir, lang_code)
    if version:
        if not lang_code:
            raise Exception("Must specify lang_code with version")
        build_dir = os.path.join(build_dir, version)

    return build_dir


def get_language_pack_metadata_filepath(lang_code, version=VERSION, is_central_server=settings.CENTRAL_SERVER):
    lang_code = lcode_to_ietf(lang_code)
    metadata_filename = "%s_metadata.json" % lang_code
    if is_central_server:
        return os.path.join(get_lp_build_dir(lang_code, version=version), metadata_filename)
    else:
        lang_code = lcode_to_django_dir(lang_code)
        return os.path.join(LOCALE_ROOT, lang_code, metadata_filename)

def get_language_pack_filepath(lang_code, version=VERSION):
    return os.path.join(LANGUAGE_PACK_ROOT, version, "%s.zip" % lcode_to_ietf(lang_code))

def get_language_pack_url(lang_code, version=VERSION):
    url = "http://%s/%s" % (
        settings.CENTRAL_SERVER_HOST,
        get_language_pack_filepath(lang_code, version=version)[len(settings.PROJECT_PATH):],
    )
    return url

def get_django_lc_message_file(lang_code, file_name="django.mo", locale_root=LOCALE_ROOT):
    return os.path.join(locale_root, lcode_to_django_dir(lang_code), "LC_MESSAGES", file_name)

class LanguageNotFoundError(Exception):
    pass


SUPPORTED_LANGUAGE_MAP = None
CACHE_VARS.append("SUPPORTED_LANGUAGE_MAP")
def get_supported_language_map(lang_code=None):
    lang_code = lcode_to_ietf(lang_code)
    global SUPPORTED_LANGUAGE_MAP
    if not SUPPORTED_LANGUAGE_MAP:
        with open(SUPPORTED_LANGUAGES_FILEPATH) as f:
            SUPPORTED_LANGUAGE_MAP = json.loads(f.read())

    if not lang_code:
        return SUPPORTED_LANGUAGE_MAP
    else:
        lang_map = defaultdict(lambda: lang_code)
        lang_map.update(SUPPORTED_LANGUAGE_MAP.get(lang_code) or {})
        return lang_map

def lang_best_name(l):
    return l.get('native_name') or l.get('ka_name') or l.get('name')

def get_supported_languages():
    return get_supported_language_map().keys()

DUBBED_VIDEO_MAP_RAW = None
CACHE_VARS.append("DUBBED_VIDEO_MAP_RAW")
DUBBED_VIDEO_MAP = None
CACHE_VARS.append("DUBBED_VIDEO_MAP")
def get_dubbed_video_map(lang_code=None, force=False):
    """
    Stores a key per language.  Value is a dictionary between video_id and (dubbed) youtube_id
    """
    global DUBBED_VIDEO_MAP, DUBBED_VIDEO_MAP_RAW, DUBBED_VIDEOS_MAPPING_FILEPATH

    if DUBBED_VIDEO_MAP is None or force:
        try:
            if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH) or force:
                try:
                    if settings.CENTRAL_SERVER:
                        # Never call commands that could fail from the distributed server.
                        #   Always create a central server API to abstract things (see below)
                        logging.debug("Generating dubbed video mappings.")
                        call_command("generate_dubbed_video_mappings", force=force)
                    else:
                        # Generate from the spreadsheet
                        response = requests.get("http://%s/api/i18n/videos/dubbed_video_map" % (settings.CENTRAL_SERVER_HOST))
                        response.raise_for_status()
                        with open(DUBBED_VIDEOS_MAPPING_FILEPATH, "wb") as fp:
                            fp.write(response.content.decode('utf-8'))  # wait until content has been confirmed before opening file.
                except Exception as e:
                    if not os.path.exists(DUBBED_VIDEOS_MAPPING_FILEPATH):
                        # Unrecoverable error, so raise
                        raise
                    elif DUBBED_VIDEO_MAP:
                        # No need to recover--allow the downstream dude to catch the error.
                        raise
                    else:
                        # We can recover by NOT forcing reload.
                        logging.warn("%s" % e)

            DUBBED_VIDEO_MAP_RAW = softload_json(DUBBED_VIDEOS_MAPPING_FILEPATH, raises=True)
        except Exception as e:
            logging.info("Failed to get dubbed video mappings; defaulting to empty.")
            DUBBED_VIDEO_MAP_RAW = {}  # setting this will avoid triggering reload on every call

        DUBBED_VIDEO_MAP = {}
        for lang_name, video_map in DUBBED_VIDEO_MAP_RAW.iteritems():
            logging.debug("Adding dubbed video map entry for %s (name=%s)" % (get_langcode_map(lang_name), lang_name))
            DUBBED_VIDEO_MAP[get_langcode_map(lang_name)] = video_map

    return DUBBED_VIDEO_MAP.get(lang_code, {}) if lang_code else DUBBED_VIDEO_MAP

YT2ID_MAP = None
CACHE_VARS.append("YT2ID_MAP")
def get_file2id_map(force=False):
    global YT2ID_MAP
    if YT2ID_MAP is None or force:
        YT2ID_MAP = {}
        for lang_code, dic in get_dubbed_video_map().iteritems():
            for english_youtube_id, dubbed_youtube_id in dic.iteritems():
                if dubbed_youtube_id in YT2ID_MAP:
                    logging.debug("conflicting entry of dubbed_youtube_id %s in %s dubbed video map" % (dubbed_youtube_id, lang_code))
                YT2ID_MAP[dubbed_youtube_id] = english_youtube_id  # assumes video id is the english youtube_id
    return YT2ID_MAP

ID2OKLANG_MAP = None
CACHE_VARS.append("ID2OKLANG_MAP")
def get_id2oklang_map(video_id, force=False):
    global ID2OKLANG_MAP
    if ID2OKLANG_MAP is None or force:
        ID2OKLANG_MAP = {}
        for lang_code, dic in get_dubbed_video_map().iteritems():
            for english_youtube_id, dubbed_youtube_id in dic.iteritems():
                cur_video_id = get_video_id(english_youtube_id)
                ID2OKLANG_MAP[cur_video_id] = ID2OKLANG_MAP.get(english_youtube_id, {})
                ID2OKLANG_MAP[cur_video_id][lang_code] = dubbed_youtube_id
    if video_id:
        # Not all IDs made it into the spreadsheet, so by default, use the video_id as the youtube_id
        return ID2OKLANG_MAP.get(video_id, {"en": get_youtube_id(video_id, None)})
    else:
        return ID2OKLANG_MAP

def get_youtube_id(video_id, lang_code=settings.LANGUAGE_CODE):
    if not lang_code:  # looking for the base/default youtube_id
        return video_id
    return get_dubbed_video_map(lang_code).get(video_id)

def get_video_id(youtube_id):
    """
    Youtube ID is assumed to be the non-english
    """
    return get_file2id_map().get(youtube_id, youtube_id)

YT2LANG_MAP = None
CACHE_VARS.append("YT2LANG_MAP")
def get_file2lang_map(force=False):
    """Map from youtube_id to language code"""
    global YT2LANG_MAP
    if YT2LANG_MAP is None or force:
        YT2LANG_MAP = {}
        for lang_code, dic in get_dubbed_video_map().iteritems():
            for dubbed_youtube_id in dic.values():
                if dubbed_youtube_id in YT2LANG_MAP:
                    # Sanity check, but must be failsafe, since we don't control these data
                    if YT2LANG_MAP[dubbed_youtube_id] == lang_code:
                        logging.warn("Duplicate entry found in %s language map for dubbed video %s" % (lang_code, dubbed_youtube_id))
                    else:
                        logging.error("Conflicting entry found in language map for video %s; overwriting previous entry of %s to %s." % (dubbed_youtube_id, YT2LANG_MAP[dubbed_youtube_id], lang_code))
                YT2LANG_MAP[dubbed_youtube_id] = lang_code
    return YT2LANG_MAP

def get_video_language(youtube_id, force=False):
    lang_code = get_file2lang_map(force=force).get(youtube_id)
    logging.debug("%s mapped to language %s" % (youtube_id, lang_code))
    return lang_code or "en"  # default to "en"

def get_srt_url(youtube_id, code):
    return settings.STATIC_URL + "srt/%s/subtitles/%s.srt" % (code, youtube_id)

def get_localized_exercise_count(lang_code, is_central_server=settings.CENTRAL_SERVER):
    exercise_dir = get_localized_exercise_dirpath(lang_code, is_central_server=is_central_server)
    all_exercises = glob.glob(os.path.join(exercise_dir, "*.html"))
    return len(all_exercises)


def get_srt_path(lang_code=None, youtube_id=None):
    """Both central and distributed servers must make these available
    at a web-accessible location.

    Now, they share that location, which was published in 0.10.2, and so cannot be changed
    (at least, not from the central-server side)

    Note also that it must use the django-version language code.
    """
    srt_path = os.path.join(settings.STATIC_ROOT, "srt")
    if lang_code:
        srt_path = os.path.join(srt_path, lcode_to_django_dir(lang_code), "subtitles")
    if youtube_id:
        srt_path = os.path.join(srt_path, youtube_id + ".srt")

    return srt_path

def get_subtitle_count(lang_code):
    all_srts = glob.glob(os.path.join(get_srt_path(lang_code=lang_code), "*.srt"))
    return len(all_srts)

CODE2LANG_MAP = None
CACHE_VARS.append("CODE2LANG_MAP")
def get_code2lang_map(lang_code=None, force=False):
    """
    """
    global LANG_LOOKUP_FILEPATH, CODE2LANG_MAP

    if force or not CODE2LANG_MAP:
        lmap = softload_json(LANG_LOOKUP_FILEPATH, logger=logging.debug)

        CODE2LANG_MAP = {}
        for lc, entry in lmap.iteritems():
            CODE2LANG_MAP[lcode_to_ietf(lc)] = entry

    return CODE2LANG_MAP.get(lang_code) if lang_code else CODE2LANG_MAP

LANG2CODE_MAP = None
CACHE_VARS.append("LANG2CODE_MAP")
def get_langcode_map(lang_name=None, force=False):
    """
    """
    global LANG_LOOKUP_FILEPATH, LANG2CODE_MAP

    if force or not LANG2CODE_MAP:
        LANG2CODE_MAP = {}

        for code, entries in get_code2lang_map(force=force).iteritems():
            for lang in entries.values():
                if lang:
                    LANG2CODE_MAP[lang.lower()] = lcode_to_ietf(code)

    return LANG2CODE_MAP.get(lang_name) if lang_name else LANG2CODE_MAP

def get_language_name(lang_code, native=False, error_on_missing=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""
    global LANG_LOOKUP_FILEPATH

    # Convert code if neccessary
    lang_code = lcode_to_ietf(lang_code)

    language_entry = get_code2lang_map(lang_code)
    if not language_entry:
        if error_on_missing:
            raise LanguageNotFoundError("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, LANG_LOOKUP_FILEPATH))
        else:
            # Fake it
            language_entry = {"name": lang_code, "native_name": lang_code}

    if not isinstance(language_entry, dict):
        return language_entry
    else:
        if not native:
            return language_entry["name"]
        else:
            return language_entry["native_name"]


def get_language_code(language, for_django=False):
    """
    Return ISO 639-1 language code full English or native language name from ;
    raise exception if it isn't hardcoded yet
    """
    global LANG_LOOKUP_FILEPATH

    lang_code = get_langcode_map().get(language.lower())
    if not lang_code:
       raise LanguageNotFoundError("We don't have language '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (language, LANG_LOOKUP_FILEPATH))
    elif for_django:
        return lcode_to_django_dir(lang_code)
    else:
        return lang_code


def lcode_to_django_lang(lang_code):
    return convert_language_code_format(lang_code, for_django=True).lower()

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
    if not lang_code:  # protect against None
        return lang_code

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

LANG_NAMES_MAP = None
CACHE_VARS.append("LANG_NAMES_MAP")
def get_language_names(lang_code=None):
    """
    Returns dictionary of names (English name, "Native" name)
    for a given language code.
    """
    global LANG_NAMES_MAP
    lang_code = lcode_to_ietf(lang_code)
    if not LANG_NAMES_MAP:
        LANG_NAMES_MAP = softload_json(LANG_LOOKUP_FILEPATH)
    return LANG_NAMES_MAP.get(lang_code) if lang_code else LANG_NAMES_MAP

INSTALLED_LANGUAGES_CACHE = None
CACHE_VARS.append("INSTALLED_LANGUAGES_CACHE")
def get_installed_language_packs(force=False):
    global INSTALLED_LANGUAGES_CACHE
    if not INSTALLED_LANGUAGES_CACHE or force:
        INSTALLED_LANGUAGES_CACHE = _get_installed_language_packs()
    return INSTALLED_LANGUAGES_CACHE

def _get_installed_language_packs():
    """
    On-disk method to show currently installed languages and meta data.
    """

    # There's always English...
    installed_language_packs = [{
        'code': 'en',
        'software_version': VERSION,
        'language_pack_version': 0,
        'percent_translated': 100,
        'subtitle_count': 0,
        'name': 'English',
        'native_name': 'English',
    }]

    # Loop through locale folders
    for locale_dir in settings.LOCALE_PATHS:
        if not os.path.exists(locale_dir):
            continue

        # Loop through folders in each locale dir
        for django_disk_code in os.listdir(locale_dir):

            # Inside each folder, read from the JSON file - language name, % UI trans, version number
            try:
                # Get the metadata
                metadata_filepath = os.path.join(locale_dir, django_disk_code, "%s_metadata.json" % lcode_to_ietf(django_disk_code))
                lang_meta = softload_json(metadata_filepath, raises=True)

                logging.debug("Found language pack %s" % (django_disk_code))
            except Exception as e:
                if isinstance(e, IOError) and e.errno == 2:
                    logging.info("Ignoring non-language pack %s in %s" % (django_disk_code, locale_dir))
                else:
                    logging.error("Error reading %s metadata (%s): %s" % (django_disk_code, metadata_filepath, e))
                continue

            installed_language_packs.append(lang_meta)

    sorted_list = sorted(installed_language_packs, key=lambda m: m['name'].lower())
    return OrderedDict([(lcode_to_ietf(val["code"]), val) for val in sorted_list])

def get_langs_with_subtitles():
    subtitles_path = get_srt_path()
    if os.path.exists(subtitles_path):
        return os.listdir(subtitles_path)
    else:
        return []

def get_langs_with_subtitle(youtube_id):
    """
    Returns a list of all language codes that contain subtitles for this video.

    Central and distributed servers store in different places, so loop differently
    """

    subtitles_path = get_srt_path()
    if os.path.exists(subtitles_path):
        installed_subtitles = [lc for lc in os.listdir(subtitles_path) if os.path.exists(get_srt_path(lc, youtube_id))]
    else:
        installed_subtitles = []
    return sorted(installed_subtitles)


def update_jsi18n_file(code="en"):
    """
    For efficieny's sake, we want to cache Django's
    js18n file.  So, generate that file here, then
    save to disk--it won't change until the next language pack update!
    """
    translation.activate(code)  # we switch the language of the whole thread
    output_dir = os.path.join(settings.STATIC_ROOT, "js", "i18n")
    ensure_dir(output_dir)
    output_file = os.path.join(output_dir, "%s.js" % code)

    request = HttpRequest()
    request.path = output_file
    request.session = {settings.LANGUAGE_COOKIE_NAME: code}

    response = javascript_catalog(request, packages=('ka-lite.locale',))
    with open(output_file, "w") as fp:
        fp.write(response.content)


def select_best_available_language(target_code, available_codes=None):
    """
    Critical function for choosing the best available language for a resource,
    given a target language code.

    This is used by video and exercise pages, for example,
    to determine what file to serve, based on available resources
    and the current requested language.
    """

    # Scrub the input
    target_code = lcode_to_django_lang(target_code)
    if available_codes is None:
        available_codes = get_installed_language_packs().keys()
    available_codes = [lcode_to_django_lang(lc) for lc in available_codes]

    # Hierarchy of language selection
    if target_code in available_codes:
        actual_code = target_code
    elif target_code.split("-", 1)[0] in available_codes:
        actual_code = target_code.split("-", 1)[0]
    elif settings.LANGUAGE_CODE in available_codes:
        actual_code = settings.LANGUAGE_CODE
    elif "en" in available_codes:
        actual_code = "en"
    elif available_codes:
        actual_code = available_codes[0]
    else:
        actual_code = None

    if actual_code != target_code:
        logging.debug("Requested code %s, got code %s" % (target_code, actual_code))
    return actual_code

def scrub_locale_paths():
    for locale_root in settings.LOCALE_PATHS:
        if not os.path.exists(locale_root):
            continue
        for lang in os.listdir(locale_root):
            # Skips if not a directory
            if not os.path.isdir(os.path.join(locale_root, lang)):
                continue
            # If it isn't crowdin/django format, keeeeeeellllllll
            if lang != lcode_to_django_dir(lang):
                logging.info("Deleting %s directory because it does not fit our language code format standards" % lang)
                shutil.rmtree(os.path.join(locale_root, lang))

def move_old_subtitles():
    locale_root = settings.LOCALE_PATHS[0]
    srt_root = os.path.join(settings.STATIC_ROOT, "srt")
    if os.path.exists(srt_root):
        logging.info("Outdated schema detected for storing srt files. Hang tight, the moving crew is on it.")
        for lang in os.listdir(srt_root):
            # Skips if not a directory
            if not os.path.isdir(os.path.join(srt_root, lang)):
                continue
            lang_srt_path = os.path.join(srt_root, lang, "subtitles/")
            lang_locale_path = os.path.join(locale_root, lang)
            ensure_dir(lang_locale_path)
            dst = os.path.join(lang_locale_path, "subtitles")

            for srt_file_path in glob.glob(os.path.join(lang_srt_path, "*.srt")):
                base_path, srt_filename = os.path.split(srt_file_path)
                if not os.path.exists(os.path.join(dst, srt_filename)):
                    ensure_dir(dst)
                    shutil.move(srt_file_path, os.path.join(dst, srt_filename))
        shutil.rmtree(srt_root)
        logging.info("Move completed.")
