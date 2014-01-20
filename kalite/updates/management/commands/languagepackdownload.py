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
from i18n.models import LanguagePack
from settings import LOG as logging
from shared.i18n import LOCALE_ROOT, lcode_to_django_dir, lcode_to_ietf, get_language_pack_metadata_filepath, get_language_pack_filepath, get_language_pack_url, get_srt_path, update_jsi18n_file
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
        "update_database",
        "add_js18n_file",
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

            # Update database with meta info
            self.next_stage("Updating database for language pack '%s'" % lang_code)
            update_database(lang_code)

            #
            self.next_stage("Creating static files for language pack '%s'" % lang_code)
            update_jsi18n_file(lang_code)

            #
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


def update_database(lang_code):
    """Create/update LanguagePack table in database based on given languages metadata"""

    lang_code = lcode_to_ietf(lang_code)
    with open(get_language_pack_metadata_filepath(lang_code)) as fp:
        metadata = json.load(fp)

    logging.info("Updating database for language pack: %s" % lang_code)

    pack = get_object_or_None(LanguagePack, code=lang_code) or LanguagePack(code=lang_code)
    for key, value in metadata.iteritems():
        setattr(pack, key, value)
    pack.save()

    logging.info("Successfully updated database.")

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

    if os.listdir(src_dir):
        logging.warn("%s is not empty; will not remove.  Please check that all subtitles were moved." % src_dir)
    else:
        logging.info("Removing empty source directory (%s)." % src_dir)
        shutil.rmtree(src_dir)
