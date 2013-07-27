import json
import os
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import subtitle_utils 
from main import topicdata
import settings
from settings import LOG as logging

LANGUAGE_LOOKUP = topicdata.LANGUAGE_LOOKUP
LANGUAGE_LIST   = topicdata.LANGUAGE_LIST


class LanguageNameDoesNotExist(Exception):

    def __str__(value):
        return "The language name doesn't exist yet. Please add it to the lookup dictionary located at static/data/languages.json"


def get_new_counts(data_path, download_path):
    """Return dictionary of srt file counts in respective download folders"""

    subtitle_counts = {}

    # index into ka-lite/locale/
    for (dirpath, languages, filenames) in os.walk(download_path):
        for lang_code in languages:
            subtitles_path = "%s%s/subtitles/" % (download_path, lang_code) 
            try:      
                count = len(os.listdir(subtitles_path))
            except:
                logging.info("No subs for %s" % lang_code)
                continue
            else: 
                lang_name = get_language_name(lang_code) 
                subtitle_counts[lang_name] = {}
                subtitle_counts[lang_name]["count"] = count
                subtitle_counts[lang_name]["code"] = lang_code
    write_new_json(subtitle_counts, data_path)
    update_language_list(subtitle_counts, data_path)


def get_language_name(lang_code):
    """Return full language name from ISO 639-1 language code, raise exception if it isn't hardcoded yet"""
    language_name = LANGUAGE_LOOKUP.get(lang_code)
    if language_name:
        logging.info("%s: %s" %(lang_code, language_name))
        return language_name
    else: 
        raise LanguageNameDoesNotExist()


def write_new_json(subtitle_counts, data_path):
    """Write JSON to file in static/data/subtitledata"""
    filename = "subtitle_counts.json"
    filepath = data_path + filename
    logging.info("Writing fresh srt counts to %s" % filepath)
    with open(filepath, 'wb') as fp:
        json.dump(subtitle_counts, fp)


def update_language_list(sub_counts, data_path):
    """Update hardcoded language codes if any supported subtitle languages aren't there."""
    for data in sub_counts.values():
        lang_code = data.get("code")
        if lang_code not in LANGUAGE_LIST:
            logging.info("Adding %s to language code list" % lang_code)
            LANGUAGE_LIST.append(lang_code)
    with open(os.path.join(data_path, "listedlanguages.json"), 'wb') as fp:
        json.dump(LANGUAGE_LIST, fp)


if __name__ == "__main__":
    get_new_counts()


