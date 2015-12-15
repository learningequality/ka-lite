"""
Management command for downloading a language pack and extracting the
contents to their correct locations.

Usage:
  contentpackretrieve download <lang>
  contentpackretrieve retrieve <lang> <packpath>
  contentpackretrieve -h | --help

"""
import urllib
import tempfile
import shutil
import zipfile

from django.core.management.base import BaseCommand

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

            extract_catalog_files(zf)
            extract_content_db(zf, lang)


def download_content_pack(fobj, lang):
    url = CONTENT_PACK_URL_TEMPLATE.format(
        version=SHORTVERSION,
        code=lang,
    )

    urllib.urlretrieve(url, filename=fobj.name)
    zf = zipfile.ZipFile(fobj.name)

    return zf


def extract_catalog_files(zf):
    pass


def extract_content_db(zf, lang):
    content_db_path = settings.CONTENT_DATABASE_PATH.format(
        channel=settings.CHANNEL,
        language=lang,
    )

    with open(content_db_path, "wb") as f:
        dbfobj = zf.open("content.db")
        shutil.copyfileobj(dbfobj, f)
