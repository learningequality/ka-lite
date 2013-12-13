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
from shared.i18n import lcode_to_django_dir, lcode_to_ietf, get_language_pack_metadata_filepath, get_language_pack_filepath, update_jsi18n_file, get_language_pack_url, get_localized_exercise_dirpath
from utils.general import ensure_dir


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
        if lcode_to_django_dir(lang_code) == settings.LANGUAGE_CODE:
            logging.info("Note: language code set to default language. This is fine (and may be intentional), but you may specify a language other than '%s' with -l" % lang_code)
        if software_version == version.VERSION:
            logging.info("Note: software version set to default version. This is fine (and may be intentional), but you may specify a software version other than '%s' with -s" % version.VERSION)


        # Download the language pack
        try:
            self.start("Downloading language pack '%s'" % lang_code)
            zip_file = get_language_pack(lang_code, software_version)

            # Unpack into locale directory
            self.next_stage("Unpacking language pack '%s'" % lang_code)
            unpack_language(lang_code, zip_file)

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

def get_language_pack(lang_code, software_version):
    """Download language pack for specified language"""

    lang_code = lcode_to_ietf(lang_code)
    logging.info("Retrieving language pack: %s" % lang_code)
    request_url = get_language_pack_url(lang_code, software_version)
    r = requests.get(request_url)
    try:
        r.raise_for_status()
    except Exception as e:
        raise CommandError(e)

    return r.content

def unpack_language(lang_code, zip_file):
    """Unpack zipped language pack into locale directory"""
    lang_code = lcode_to_django_dir(lang_code)

    logging.info("Unpacking new translations")
    ensure_dir(os.path.join(LOCALE_ROOT, lang_code, "LC_MESSAGES"))

    ## Unpack into temp dir
    z = zipfile.ZipFile(StringIO(zip_file))
    z.extractall(os.path.join(LOCALE_ROOT, lang_code))

def move_dubbed_video_map(lang_code):
    lang_pack_location = os.path.join(LOCALE_ROOT, lang_code)
    dvm_filepath = os.path.join(lang_pack_location, "dubbed_videos", os.path.basename(DUBBED_VIDEOS_MAPPING_FILEPATH))
    if not os.path.exists(dvm_filepath):
        logging.error("Could not find downloaded dubbed video filepath: %s" % dvm_filepath)
    else:
        ensure_dir(os.path.dirname(DUBBED_VIDEOS_MAPPING_FILEPATH))
        shutil.move(dvm_filepath, DUBBED_VIDEOS_MAPPING_FILEPATH)

def move_exercises(lang_code):
    src_exercise_dir = get_localized_exercise_dirpath(lang_code, is_central_server=True)
    dest_exercise_dir = get_localized_exercise_dirpath(lang_code, is_central_server=False)
    if not os.path.exists(src_exercise_dir):
        logging.warn("Could not find downloaded exercises; skipping: %s" % src_exercise_dir)
    else:
        logging.info("Moving downloaded exercises to %s" % dest_exercise_dir)
        shutil.move(src_exercise_dir, dest_exercise_dir)

def move_srts(lang_code):
    """
    Srts live in the locale directory, but that's not exposed at any URL.  So instead,
    we have to move the srts out to /static/subtitles/[lang_code]/
    """
    lang_code_ietf = lcode_to_ietf(lang_code)
    lang_code_django = lcode_to_django_dir(lang_code)

    subtitles_static_dir = os.path.join(settings.STATIC_ROOT, "subtitles")
    srt_static_dir = os.path.join(subtitles_static_dir, lang_code_ietf)
    srt_locale_dir = os.path.join(LOCALE_ROOT, lang_code_django, "subtitles")
    ensure_dir(srt_static_dir)

    lang_subtitles = glob.glob(os.path.join(srt_locale_dir, "*.srt"))
    logging.debug("Moving %d subtitles from %s to %s" % (len(lang_subtitles), srt_locale_dir, srt_static_dir))

    for fil in lang_subtitles:
        srt_dest_path = os.path.join(srt_static_dir, os.path.basename(fil))
        if os.path.exists(srt_dest_path):
            os.remove(srt_dest_path)
        shutil.move(fil, srt_dest_path)
