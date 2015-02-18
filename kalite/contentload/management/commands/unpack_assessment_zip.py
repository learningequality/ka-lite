import StringIO
import json
import requests
import os
import urlparse
import zipfile
from fle_utils.general import ensure_dir

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

KHAN_DATA_PATH = os.path.join(
    settings.CONTENT_DATA_PATH,
    "khan",
)

KHAN_CONTENT_PATH = os.path.join(
    settings.CONTENT_ROOT,
    "khan"
)

ASSESSMENT_ITEMS_PATH = os.path.join(KHAN_DATA_PATH, "assessmentitems.json")

logging = settings.LOG

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError("We expect only one argument; the location of the zip.")

        ziplocation = args[0]

        if is_valid_url(ziplocation):  # url; download the zip
            logging.warn("Downloading assessment item data from a remote server. Please be patient; this file is big, so this may take some time...")
            r = requests.get(ziplocation)
            r.raise_for_status()
            f = StringIO.StringIO(r.content)
        else:                   # file; just open it normally
            f = open(ziplocation, "r")

        zf = zipfile.ZipFile(f, "r")

        extract_assessment_items_to_data_dir(zf)
        unpack_zipfile_to_khan_content(zf)


def extract_assessment_items_to_data_dir(zf):
    zf.extract("assessmentitems.json", KHAN_DATA_PATH)


def unpack_zipfile_to_khan_content(zf):
    dir = settings.ASSESSMENT_ITEMS_RESOURCES_DIR
    ensure_dir(dir)
    zf.extractall(dir)


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
