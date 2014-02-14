"""
CENTRAL SERVER ONLY

This command is used to cache srt files on the central server. It uses
the mapping generate by generate_subtitle_map to make requests of the
Amara API.

NOTE: srt map deals with amara, so uses ietf codes (e.g. en-us). However,
  when directories are created, we use django-style directories (e.g. en_US)
"""
import glob
import os
import requests
import shutil
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from i18n import get_dubbed_video_map, lcode_to_ietf, lcode_to_django_lang, get_localized_exercise_dirpath
from main.topic_tools import get_node_cache
from settings import LOG as logging
from utils.general import ensure_dir

AVAILABLE_EXERCISE_LANGUAGE_CODES = ["da", "he", "pt-BR", "tr", "es", "fr"]

class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitles/srts_download_status.json"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=None,
                    metavar="LANG_CODE",
                    help="Specify a particular language code (e.g. en-us) to download subtitles for. Can be used with -f to update previously downloaded subtitles."),
        make_option('-i', '--exercise-ids',
                    action='store',
                    dest='exercise_ids',
                    default=None,
                    metavar="exercise_ids",
                    help="Download the specified exercises only"),
        make_option('-t', '--topic-id',
                    action='store',
                    dest='topic_id',
                    default=None,
                    metavar="TOPIC_ID",
                    help="Download all videos from a topic"),
        make_option('-o', '--format',
                    action='store_true',
                    dest='format',
                    default="mp4",
                    metavar="FORMAT",
                    help="Specify the format to convert the video to"),
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    metavar="FORCE",
                    help="Force re-downloading of previously downloaded subtitles to refresh the repo. Can be used with -l. Default behavior is to not re-download subtitles we already have."),
    )


    def handle(self, *args, **options):
        if not options["lang_code"]:
            raise CommandError("You must specify a language code.")


        lang_code = lcode_to_ietf(options["lang_code"])
        if lang_code not in AVAILABLE_EXERCISE_LANGUAGE_CODES:
            logging.info("No exercises available for language %s" % lang_code)

        else:
            # Get list of exercises
            exercise_ids = options["exercise_ids"].split(",") if options["exercise_ids"] else None
            exercise_ids = exercise_ids or ([ex["id"] for ex in get_topic_exercises(topic_id=options["topic_id"])] if options["topic_id"] else None)
            exercise_ids = exercise_ids or get_node_cache("Exercise").keys()

            # Download the exercises
            for exercise_id in exercise_ids:
                scrape_exercise(exercise_id=exercise_id, lang_code=lang_code, force=options["force"])

        logging.info("Process complete.")

def get_exercise_filepath(exercise_id, lang_code=None, is_central_server=settings.CENTRAL_SERVER):
    if settings.CENTRAL_SERVER:
        exercise_filename = "%s.%s" % (exercise_id, "html")
        exercise_localized_root = get_localized_exercise_dirpath(lang_code)
        exercise_dest_filepath = os.path.join(exercise_localized_root, exercise_filename)
    else:
        raise NotImplementedError

    return exercise_dest_filepath

def scrape_exercise(exercise_id, lang_code, force=False):
    ietf_lang_code = lcode_to_ietf(lang_code)

    exercise_dest_filepath = get_exercise_filepath(exercise_id, lang_code=lang_code)
    exercise_localized_root = os.path.dirname(exercise_dest_filepath)

    if os.path.exists(exercise_dest_filepath) and not force:
        return

    exercise_url = "https://es.khanacademy.org/khan-exercises/exercises/%s.html?lang=%s" % (exercise_id, ietf_lang_code)
    logging.info("Retrieving exercise %s from %s" % (exercise_id, exercise_url))

    try:
        ensure_dir(exercise_localized_root)

        resp = requests.get(exercise_url)
        resp.raise_for_status()
        with open(exercise_dest_filepath, "wb") as fp:
            fp.write(resp.content)
    except Exception as e:
        logging.error("Failed to download %s: %s" % (exercise_url, e))
