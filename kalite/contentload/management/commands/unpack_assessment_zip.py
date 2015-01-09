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

ASSESSMENT_ITEMS_PATH = os.path.join(KHAN_DATA_PATH, "assessment_items.json")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError("We expect only one argument; the location of the zip.")

        ziplocation = args[0]

        if is_valid_url(ziplocation):  # url; download the zip
            r = requests.get(ziplocation)
            r.raise_for_status()
            f = StringIO.StringIO(r.content)
        else:                   # file; just open it normally
            f = open(ziplocation, "r")

        zf = zipfile.ZipFile(f, "r")

        extract_assessment_items_to_data_dir(zf)
        unpack_zipfile_to_khan_content(zf)


def extract_assessment_items_to_data_dir(zf):
    with open(ASSESSMENT_ITEMS_PATH) as f:
        old_assessment_items = json.load(f)

    zipped_assessment_items = zf.open("assessment_items.json")
    new_assessment_items = json.load(zipped_assessment_items)
    old_assessment_items.update(new_assessment_items)

    with open(ASSESSMENT_ITEMS_PATH, "w") as f:
        json.dump(old_assessment_items, f, indent=4)


def unpack_zipfile_to_khan_content(zf):
    dir = settings.ASSESSMENT_ITEMS_RESOURCES_DIR
    ensure_dir(dir)
    zf.extractall(dir)


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
