"""
Management command for downloading a language pack and extracting the
contents to their correct locations.

Usage:
  contentpackretrieve download <lang>
  contentpackretrieve retrieve <lang> <packpath>
  contentpackretrieve -h | --help

"""
import json
import os
import urllib
import tempfile
import shutil
import zipfile

from django.core.management.base import BaseCommand
from django.core.management import call_command

from fle_utils.general import ensure_dir

from kalite.i18n.base import lcode_to_django_lang, get_po_filepath, get_locale_path
from kalite.topic_tools import settings

from kalite.version import SHORTVERSION

CONTENT_PACK_URL_TEMPLATE = ("http://pantry.learningequality.org/downloads" +
                             "/ka-lite/{version}/content/contentpacks/{code}.zip")


class Command(BaseCommand):

    def handle(self, *args, **options):

        # TODO: change the codepath depending on whether they want to download
        # or simply extract a content pack.

        # parse out the options and raise errors if necessary
        lang = args[0]

        with tempfile.NamedTemporaryFile() as f:
            zf = download_content_pack(f, lang)

            extract_catalog_files(zf, lang)
            extract_content_db(zf, lang)
            extract_content_pack_metadata(zf, lang)

            call_command("annotate_content_items")


def extract_content_pack_metadata(zf, lang):
    # stub for now, until we implement metadata creation on the maker side.
    metadata_path = os.path.join(get_locale_path(lang), "{lang}_metadata.json".format(lang=lang))
    barebones_metadata = {
        "code": lang,
        'software_version': SHORTVERSION,
        'language_pack_version': 1,
        'percent_translated': 100,
        'subtitle_count': 0,
        "name": "DEBUG",
        'native_name': 'DEBUG',
    }

    with open(metadata_path, "wb") as f:
        json.dump(barebones_metadata, f)


def download_content_pack(fobj, lang):
    url = CONTENT_PACK_URL_TEMPLATE.format(
        version=SHORTVERSION,
        code=lang,
    )

    urllib.urlretrieve(url, filename=fobj.name)
    zf = zipfile.ZipFile(fobj.name)

    return zf


def extract_catalog_files(zf, lang):
    lang = lcode_to_django_lang(lang)
    modir = get_po_filepath(lang)
    ensure_dir(modir)

    filename_mapping = {"frontend.mo": "djangojs.mo",
                        "backend.mo": "django.mo"}

    for zipmo, djangomo in filename_mapping.items():
        zipmof = zf.open(zipmo)
        mopath = os.path.join(modir, djangomo)
        print("writing to %s" % mopath)
        with open(mopath, "wb") as djangomof:
            shutil.copyfileobj(zipmof, djangomof)


def extract_content_db(zf, lang):
    content_db_path = settings.CONTENT_DATABASE_PATH.format(
        channel=settings.CHANNEL,
        language=lang,
    )

    with open(content_db_path, "wb") as f:
        dbfobj = zf.open("content.db")
        shutil.copyfileobj(dbfobj, f)
