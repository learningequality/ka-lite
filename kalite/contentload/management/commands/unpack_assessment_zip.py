import StringIO
import requests
import os
import urlparse
import zipfile
from fle_utils.general import ensure_dir

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


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

        unpack_zipfile_to_khan_content(zf)


def extract_assessment_items_to_data_dir(zf):
    khan_data_path = os.path.join(settings.CONTENT_DATA_PATH, "khan")
    assessment_items_path = os.path.join(khan_data_path, "assessment_items.json")
    zf.extract("assessment_items.json", assessment_items_path)


def unpack_zipfile_to_khan_content(zf):
    dir = settings.ASSESSMENT_ITEMS_RESOURCES_DIR
    ensure_dir(dir)
    zf.extractall(dir)


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
