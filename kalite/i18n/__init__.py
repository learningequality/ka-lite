"""
i18n defines language
Utility functions for i18n related tasks on the distributed server
"""
import json
import os
import re
import requests
import shutil
from collections_local_copy import OrderedDict, defaultdict

from django.conf import settings; logging = settings.LOG
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
from fle_utils.config.models import Settings
from fle_utils.general import ensure_dir, softload_json
from kalite.version import VERSION

CACHE_VARS = []

DUBBED_VIDEOS_MAPPING_FILEPATH = os.path.join(settings.I18N_DATA_PATH, "dubbed_video_mappings.json")
LOCALE_ROOT = settings.LOCALE_PATHS[0]

class LanguageNotFoundError(Exception):
    pass


def get_localized_exercise_dirpath(lang_code):
    ka_lang_code = lang_code.lower()
    return os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises", ka_lang_code)


def get_locale_path(lang_code=None):
    """returns the location of the given language code, or the default locale root
    if none is provided."""
    global LOCALE_ROOT

    if not lang_code:
        return LOCALE_ROOT
    else:
        return os.path.join(LOCALE_ROOT, lcode_to_django_dir(lang_code))

def get_po_filepath(lang_code, filename=None):
    """Return the LC_MESSAGES directory for the language code, with an optional filename appended."""
    base_dirpath = os.path.join(get_locale_path(lang_code=lang_code), "LC_MESSAGES")
    return (filename and os.path.join(base_dirpath, filename)) or base_dirpath


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


LANG2CODE_MAP = None
CACHE_VARS.append("LANG2CODE_MAP")
def get_langcode_map(lang_name=None, force=False):
    """
    """
    global LANG2CODE_MAP

    if force or not LANG2CODE_MAP:
        LANG2CODE_MAP = {}

        for code, entries in get_code2lang_map(force=force).iteritems():
            for lang in entries.values():
                if lang:
                    LANG2CODE_MAP[lang.lower()] = lcode_to_ietf(code)

    return LANG2CODE_MAP.get(lang_name) if lang_name else LANG2CODE_MAP


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
    """Accepts lang_code in ietf format"""
    if not lang_code:  # looking for the base/default youtube_id
        return video_id
    return get_dubbed_video_map(lcode_to_ietf(lang_code)).get(video_id, video_id)


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
                if dubbed_youtube_id in YT2LANG_MAP and YT2LANG_MAP[dubbed_youtube_id] != lang_code:
                    # Sanity check, but must be failsafe, since we don't control these data
                    logging.error("Conflicting entry found in language map for video %s; overwriting previous entry of %s to %s." % (dubbed_youtube_id, YT2LANG_MAP[dubbed_youtube_id], lang_code))
                YT2LANG_MAP[dubbed_youtube_id] = lang_code
    return YT2LANG_MAP


def get_video_language(youtube_id, force=False):
    lang_code = get_file2lang_map(force=force).get(youtube_id)
    logging.debug("%s mapped to language %s" % (youtube_id, lang_code))
    return lang_code or "en"  # default to "en"


def get_srt_url(youtube_id, code):
    return settings.STATIC_URL + "srt/%s/subtitles/%s.srt" % (code, youtube_id)


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


CODE2LANG_MAP = None
CACHE_VARS.append("CODE2LANG_MAP")
def get_code2lang_map(lang_code=None, force=False):
    """Given a language code, returns metadata about that language."""
    global CODE2LANG_MAP

    if force or not CODE2LANG_MAP:
        lmap = softload_json(settings.LANG_LOOKUP_FILEPATH, logger=logging.debug)

        CODE2LANG_MAP = {}
        for lc, entry in lmap.iteritems():
            CODE2LANG_MAP[lcode_to_ietf(lc)] = entry

    return CODE2LANG_MAP.get(lang_code) if lang_code else CODE2LANG_MAP


def get_language_name(lang_code, native=None, error_on_missing=False):
    """Return full English or native language name from ISO 639-1 language code; raise exception if it isn't hardcoded yet"""

    # Convert code if neccessary
    lang_code = lcode_to_ietf(lang_code)

    language_entry = get_code2lang_map(lang_code)
    if not language_entry:
        if error_on_missing:
            raise LanguageNotFoundError("We don't have language code '%s' saved in our lookup dictionary (location: %s). Please manually add it before re-running this command." % (lang_code, settings.LANG_LOOKUP_FILEPATH))
        else:
            # Fake it
            language_entry = {"name": lang_code, "native_name": lang_code}

    if not isinstance(language_entry, dict):
        return language_entry
    elif native is None:  # choose ourselves
        return language_entry.get('native_name') or language_entry.get('ka_name') or language_entry.get('name')
    elif not native:
        return language_entry.get("name")
    else:
        return language_entry.get("native_name")


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


def get_default_language():
    """Returns: the default language (ietf-formatted language code)"""
    return Settings.get("default_language") or settings.LANGUAGE_CODE or "en"


def set_default_language(lang_code):
    """Sets the default language"""
    Settings.set("default_language", lcode_to_ietf(lang_code))


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
