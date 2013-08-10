import json
import os
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import subtitle_utils

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../../"
sys.path = [PROJECT_PATH] + sys.path

from main import topicdata
import settings

LANGUAGE_LOOKUP = topicdata.LANGUAGE_LOOKUP
LANGUAGE_LIST = topicdata.LANGUAGE_LIST

data_path = settings.DATA_PATH + "subtitledata/"

logger = subtitle_utils.setup_logging("generate_subtitle_counts")


class LanguageNameDoesNotExist(Exception):

    def __str__(value):
        return "The language name doesn't exist yet. Please add it to the lookup dictionary located at static/data/languages.json"


def get_new_counts():
    """Return dictionary of srt file counts in static folder organized by language"""
    srt_filepath = data_path + "srts_by_language/"
    language_files = os.listdir(srt_filepath) 
    subtitle_counts = {}

    for f in language_files:
        count = len(json.loads(open(srt_filepath + f).read())["srt_files"])
        lang_code = f.rstrip(".json")
        lang_name = get_language_name(lang_code)
        subtitle_counts[lang_name] = {}
        subtitle_counts[lang_name]["count"] = count
        subtitle_counts[lang_name]["code"] = lang_code
    write_new_json(subtitle_counts)
    update_language_list(subtitle_counts)


def get_language_name(lang_code):
    """Return full language name from ISO 639-1 language code, raise exception if it isn't hardcoded yet"""
    language_name = LANGUAGE_LOOKUP.get(lang_code)
    if language_name:
        logger.info("%s: %s" % (lang_code, language_name))
        return language_name
    else:
        raise LanguageNameDoesNotExist()


def write_new_json(subtitle_counts):
    """Write JSON to file in static/data/subtitledata"""
    filename = "subtitle_counts.json"
    filepath = data_path + filename
    logger.info("Writing fresh srt counts to %s" % filepath)
    with open(filepath, 'wb') as fp:
        json.dump(subtitle_counts, fp)


def update_language_list(sub_counts):
    """Update hardcoded language codes if any supported subtitle languages aren't there."""
    for data in sub_counts.values():
        lang_code = data.get("code")
        if lang_code not in LANGUAGE_LIST:
            logger.info("Adding %s to language code list" % lang_code)
            LANGUAGE_LIST.append(lang_code)
    with open(os.path.join(settings.DATA_PATH, "listedlanguages.json"), 'wb') as fp:
        json.dump(LANGUAGE_LIST, fp)


def update_srt_availability():
    """Update maps in srts_by_lanugage with ids of downloaded subs"""
    srts_path = settings.STATIC_ROOT + "srt/"
    for (dirpath, languages, filenames) in os.walk(srts_path):
        for lang_code in languages:
            lang_srts_path = srts_path + lang_code + "/"
            files = os.listdir(lang_srts_path)
            yt_ids = [f.rstrip(".srt") for f in files]
            srts_dict = {
                "srt_files": yt_ids
            }
            base_path = data_path + "srts_by_language/"
            subtitle_utils.ensure_dir(base_path)
            filename = "%s.json" % lang_code
            filepath = base_path + filename
            with open(filepath, 'wb') as fp:
                json.dump(srts_dict, fp)
    get_new_counts()


if __name__ == "__main__":
    update_srt_availability()
