import glob
import json
import os
import requests
import shutil
import sys
import zipfile
from optparse import make_option
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import settings
import version
from .classes import UpdatesStaticCommand
from i18n.models import LanguagePack
from settings import LOG as logging
from shared.i18n import convert_language_code_format, update_jsi18n_file
from utils.general import ensure_dir


LOCALE_ROOT = settings.LOCALE_PATHS[0]

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

        code = convert_language_code_format(options["lang_code"])
        software_version = options["software_version"]
        if code == settings.LANGUAGE_CODE:
            logging.info("Note: language code set to default language. This is fine (and may be intentional), but you may specify a language other than '%s' with -l" % code)
        if software_version == version.VERSION:
            logging.info("Note: software version set to default version. This is fine (and may be intentional), but you may specify a software version other than '%s' with -s" % version.VERSION)


        # Download the language pack
        try:
            self.start("Downloading language pack '%s'" % code)
            zip_file = get_language_pack(code, software_version)
        except CommandError as e: # 404
            sys.exit('404 Not found: Could not download language pack file %s ' % _language_pack_url(code, software_version))

        # Unpack into locale directory
        self.next_stage("Unpacking language pack '%s'" % code)
        unpack_language(code, zip_file)

        # Update database with meta info
        self.next_stage("Updating database for language pack '%s'" % code)
        update_database(code)

        #
        self.next_stage("Creating static files for language pack '%s'" % code)
        update_jsi18n_file(code)

        #
        move_srts(code)
        self.complete("Finished processing language pack %s" % code)

def get_language_pack(code, software_version):
    """Download language pack for specified language"""

    logging.info("Retrieving language pack: %s" % code)
    request_url = _language_pack_url(code, software_version)
    r = requests.get(request_url)
    try:
        r.raise_for_status()
    except Exception as e:
        raise CommandError(e)

    return r.content

def _language_pack_url(code, software_version):
    return "http://%s/static/language_packs/%s/%s.zip" % (settings.CENTRAL_SERVER_HOST, software_version, code)

def unpack_language(code, zip_file):
    """Unpack zipped language pack into locale directory"""

    logging.info("Unpacking new translations")
    ensure_dir(os.path.join(LOCALE_ROOT, code, "LC_MESSAGES"))

    ## Unpack into temp dir
    z = zipfile.ZipFile(StringIO(zip_file))
    z.extractall(os.path.join(LOCALE_ROOT, code))


def update_database(code):
    """Create/update LanguagePack table in database based on given languages metadata"""

    metadata = json.loads(open(os.path.join(LOCALE_ROOT, code, "%s_metadata.json" % code)).read())

    logging.info("Updating database for language pack: %s" % code)

    pack, created = LanguagePack.objects.get_or_create(
        code=code,
        name=metadata["name"],
        software_version=metadata["software_version"]
    )

    for key, value in metadata.items():
        setattr(pack, key, value)
    pack.save()

    logging.info("Successfully updated database.")

def move_srts(code):
    """
    Srts live in the locale directory, but that's not exposed at any URL.  So instead,
    we have to move the srts out to /static/subtitles/[code]/
    """
    subtitles_static_dir = os.path.join(settings.STATIC_ROOT, "subtitles")
    srt_static_dir = os.path.join(subtitles_static_dir, code)
    srt_locale_dir = os.path.join(LOCALE_ROOT, code, "subtitles")

    ensure_dir(srt_static_dir)
    for fil in glob.glob(os.path.join(srt_locale_dir, "*.srt")):
        srt_dest_path = os.path.join(srt_static_dir, os.path.basename(fil))
        if os.path.exists(srt_dest_path):
            os.remove(srt_dest_path)
        shutil.move(fil, srt_dest_path)
