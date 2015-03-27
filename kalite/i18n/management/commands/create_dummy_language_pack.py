"""

The create_dummy_language_pack command downloads the 'en' language
pack from the central server and creates a new language pack based on
that. Make sure you have internet!

"""

import accenting
import json
import os
import polib
import requests
import sys
import tempfile
import zipfile
from cStringIO import StringIO

from django.conf import settings
from django.core.management.base import NoArgsCommand

from fle_utils.general import ensure_dir
from kalite.i18n import get_language_pack_url, get_locale_path, update_jsi18n_file
from kalite.version import VERSION

logging = settings.LOG

BASE_LANGUAGE_PACK = "de"       # language where we base the dummy langpack from
TARGET_LANGUAGE_PACK = "eo"     # what the "dummy" language's language code. Will be. Sorry, Esperantists.
TARGET_LANGUAGE_DIR = get_locale_path(TARGET_LANGUAGE_PACK)
MO_FILE_LOCATION = os.path.join(TARGET_LANGUAGE_DIR, "LC_MESSAGES")
TARGET_LANGUAGE_METADATA_PATH = os.path.join(
    TARGET_LANGUAGE_DIR,
    "%s_metadata.json" % TARGET_LANGUAGE_PACK,
)


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        logging.info("Creating a debugging language pack, with %s language code." % TARGET_LANGUAGE_PACK)
        langpack_zip = download_language_pack(BASE_LANGUAGE_PACK)
        django_mo_contents, djangojs_mo_contents = retrieve_mo_files(langpack_zip)
        dummy_django_mo, dummy_djangojs_mo = (create_mofile_with_dummy_strings(django_mo_contents, filename="django.mo"),
                                              create_mofile_with_dummy_strings(djangojs_mo_contents, filename="djangojs.mo"))
        logging.debug("Creating i18n JS file for %s" % TARGET_LANGUAGE_PACK)
        update_jsi18n_file(code=TARGET_LANGUAGE_PACK)
        logging.info("Finished creating debugging language pack %s." % TARGET_LANGUAGE_PACK)


def download_language_pack(lang):
    logging.debug("Downloading base language pack %s for creating the debugging language." % BASE_LANGUAGE_PACK)
    url = get_language_pack_url(lang)

    try:
        logging.debug("Downloading from {url}.".format(url=url))
        resp = requests.get(url)
        resp.raise_for_status()
    except requests.ConnectionError as e:
        logging.error("Error downloading %s language pack: %s" % (lang, e))
        sys.exit(1)

    logging.debug("Successfully downloaded base language pack %s" % lang)
    return zipfile.ZipFile(StringIO(resp.content))


def retrieve_mo_files(langpack_zip):
    return (langpack_zip.read("LC_MESSAGES/django.mo"),
            langpack_zip.read("LC_MESSAGES/djangojs.mo"))


def create_mofile_with_dummy_strings(filecontents, filename):

    logging.debug("Creating %s if it does not exist yet." % MO_FILE_LOCATION)
    ensure_dir(MO_FILE_LOCATION)

    # create the language metadata file. Needed for KA Lite to
    # actually detect the language
    barebones_metadata = {
        "code": TARGET_LANGUAGE_PACK,
        'software_version': VERSION,
        'language_pack_version': 1,
        'percent_translated': 100,
        'subtitle_count': 0,
        "name": "DEBUG",
        'native_name': 'DEBUG',
    }

    logging.debug("Creating fake metadata json for %s." % TARGET_LANGUAGE_PACK)
    with open(TARGET_LANGUAGE_METADATA_PATH, "w") as f:
        json.dump(barebones_metadata, f)

    # Now create the actual MO files

    mo_file_path = os.path.join(MO_FILE_LOCATION, filename)
    po_file_path = "{po_path}.po".format(po_path=os.path.splitext(mo_file_path)[0])

    logging.debug("Creating accented %s for %s." % (filename, TARGET_LANGUAGE_PACK))
    with open(mo_file_path, "w") as f:
        f.write(filecontents)

    mofile = polib.mofile(mo_file_path)
    for moentry in mofile:
        accenting.convert_msg(moentry)
    mofile.save(fpath=mo_file_path)
    mofile.save_as_pofile(fpath=po_file_path)

    logging.debug("Finished creating %s for %s." % (filename, TARGET_LANGUAGE_PACK))
