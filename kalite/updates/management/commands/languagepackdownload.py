import glob
import json
import os
import requests
import shutil
import sys
import zipfile
from annoying.functions import get_object_or_None
from optparse import make_option
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import settings
import version
from .classes import UpdatesStaticCommand
from settings import LOG as logging
from shared.i18n import LOCALE_ROOT, DUBBED_VIDEOS_MAPPING_FILEPATH
from shared.i18n import get_language_pack_metadata_filepath, get_language_pack_filepath, get_language_pack_url, get_localized_exercise_dirpath, get_srt_path
from shared.i18n import lcode_to_django_dir, lcode_to_ietf, update_jsi18n_file
from utils.general import ensure_dir
from utils.internet import callback_percent_proxy, download_file

class Command(UpdatesStaticCommand):
    help = "Download language pack requested from central server"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=settings.LANGUAGE_CODE,
                    metavar="LANG_CODE",
                    help="Specify a particular language code to download language pack for."),
        make_option('-s', '--software_version',
                    action='store',
                    dest='software_version',
                    default=version.VERSION,
                    metavar="SOFT_VERS",
                    help="Specify the software version to download a language pack for."),
    )

    stages = (
        "download_language_pack",
        "unpack_language_pack",
        "add_js18n_file",
        "move_files",
    )

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on distributed servers server.")

        lang_code = lcode_to_ietf(options["lang_code"])
        software_version = options["software_version"]
        logging.info("Downloading language pack for lang_code=%s, software_version=%s" % (lang_code, software_version))

        # Download the language pack
        try:
            self.start("Downloading language pack '%s'" % lang_code)
            zip_filepath = get_language_pack(lang_code, software_version, callback=self.cb)

            # Unpack into locale directory
            self.next_stage("Unpacking language pack '%s'" % lang_code)
            unpack_language(lang_code, zip_filepath=zip_filepath)

            #
            self.next_stage("Creating static files for language pack '%s'" % lang_code)
            update_jsi18n_file(lang_code)


            self.next_stage("Moving files to their appropriate local disk locations.")
            move_dubbed_video_map(lang_code)
            move_exercises(lang_code)
            move_srts(lang_code)

            self.complete("Finished processing language pack %s" % lang_code)
        except Exception as e:
            self.cancel(stage_status="error", notes="Error: %s" % e)
            raise

    def cb(self, percent):
        self.update_stage(stage_percent=percent/100.)

def get_language_pack(lang_code, software_version, callback):
    """Download language pack for specified language"""

    lang_code = lcode_to_ietf(lang_code)
    logging.info("Retrieving language pack: %s" % lang_code)
    request_url = get_language_pack_url(lang_code, software_version)
    path, response = download_file(request_url, callback=callback_percent_proxy(callback))
    return path

def unpack_language(lang_code, zip_filepath=None, zip_fp=None, zip_data=None):
    """Unpack zipped language pack into locale directory"""
    lang_code = lcode_to_django_dir(lang_code)

    logging.info("Unpacking new translations")
    ensure_dir(os.path.join(LOCALE_ROOT, lang_code, "LC_MESSAGES"))

    ## Unpack into temp dir
    z = zipfile.ZipFile(zip_fp or (StringIO(zip_data) if zip_data else open(zip_filepath, "rb")))
    z.extractall(os.path.join(LOCALE_ROOT, lang_code))

def move_dubbed_video_map(lang_code):
    lang_pack_location = os.path.join(LOCALE_ROOT, lang_code)
    dvm_filepath = os.path.join(lang_pack_location, "dubbed_videos", os.path.basename(DUBBED_VIDEOS_MAPPING_FILEPATH))
    if not os.path.exists(dvm_filepath):
        logging.error("Could not find downloaded dubbed video filepath: %s" % dvm_filepath)
    else:
        logging.debug("Moving dubbed video map to %s" % DUBBED_VIDEOS_MAPPING_FILEPATH)
        ensure_dir(os.path.dirname(DUBBED_VIDEOS_MAPPING_FILEPATH))
        shutil.move(dvm_filepath, DUBBED_VIDEOS_MAPPING_FILEPATH)

def move_exercises(lang_code):
    src_exercise_dir = get_localized_exercise_dirpath(lang_code, is_central_server=True)
    dest_exercise_dir = get_localized_exercise_dirpath(lang_code, is_central_server=False)
    if not os.path.exists(src_exercise_dir):
        logging.warn("Could not find downloaded exercises; skipping: %s" % src_exercise_dir)
    else:
        # Move over one at a time, to combine with any other resources that were there before.
        ensure_dir(dest_exercise_dir)
        all_exercise_files = glob.glob(os.path.join(src_exercise_dir, "*.html"))
        logging.info("Moving %d downloaded exercises to %s" % (len(all_exercise_files), dest_exercise_dir))

        for exercise_file in all_exercise_files:
            shutil.move(exercise_file, os.path.join(dest_exercise_dir, os.path.basename(exercise_file)))

def move_srts(lang_code):
    """
    Srts live in the locale directory, but that's not exposed at any URL.  So instead,
    we have to move the srts out to /static/subtitles/[lang_code]/
    """
    lang_code_ietf = lcode_to_ietf(lang_code)
    lang_code_django = lcode_to_django_dir(lang_code)

    subtitles_static_dir = os.path.join(settings.STATIC_ROOT, "subtitles")
    src_dir = os.path.join(LOCALE_ROOT, lang_code_django, "subtitles")
    dest_dir = get_srt_path(lang_code_django)
    ensure_dir(dest_dir)

    lang_subtitles = glob.glob(os.path.join(src_dir, "*.srt"))
    logging.info("Moving %d subtitles from %s to %s" % (len(lang_subtitles), src_dir, dest_dir))

    for fil in lang_subtitles:
        srt_dest_path = os.path.join(dest_dir, os.path.basename(fil))
        if os.path.exists(srt_dest_path):
            os.remove(srt_dest_path)
        shutil.move(fil, srt_dest_path)

    if not os.path.exists(src_dir):
        pass
    elif os.listdir(src_dir):
        logging.warn("%s is not empty; will not remove.  Please check that all subtitles were moved." % src_dir)
    else:
        logging.info("Removing empty source directory (%s)." % src_dir)
        shutil.rmtree(src_dir)
