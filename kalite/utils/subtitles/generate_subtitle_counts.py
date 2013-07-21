import json
import os
import sys

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from utils.subtitles import subtitle_utils 

import settings

data_path = settings.DATA_PATH + "subtitledata/"

logger = subtitle_utils.setup_logging("generate_subtitle_counts")


class LanguageNameDoesNotExist(Exception):

    def __str__(value):
        return "The language name doesn't exist yet. Please add it to the lookup dictionary located at static/data/languages.json"


def get_new_counts():
    """Return dictionary of srt file counts in respective locale folders"""
    locale_path = settings.LOCALE_PATHS[0]  # ka-lite/locale/

    subtitle_counts = {}
    # index into ka-lite/locale/
    for (dirpath, languages, filenames) in os.walk(locale_path):
        for lang_code in languages:
            subtitles_path = "%s%s/subtitles/" % (locale_path, lang_code) 
            try:      
                count = len(os.listdir(subtitles_path))
            except:
                logger.info("No subs for %s" % lang_code)
                continue
            else: 
                lang_name = get_language_name(lang_code) 
                subtitle_counts[lang_name] = {}
                subtitle_counts[lang_name]["count"] = count
                subtitle_counts[lang_name]["code"] = lang_code
    write_new_json(subtitle_counts)


def get_language_name(lang_code):
    """Return full language name from ISO 639-1 language code, raise exception if it isn't hardcoded yet"""
    languages = json.loads(open(data_path + "../languages.json").read())
    language_name = languages.get(lang_code)
    if language_name:
        logger.info("%s: %s" %(lang_code, language_name))
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

