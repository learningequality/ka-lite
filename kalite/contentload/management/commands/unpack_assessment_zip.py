import StringIO
import requests
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
            zf = StringIO.StringIO(r.content)
        else:                   # file; just open it normally
            zf = open(ziplocation, "r")

        unpack_zipfile_to_khan_content(zf)


def unpack_zipfile_to_khan_content(zf):
    zf.extractall(settings.ASSESSMENT_ITEMS_RESOURCES_DIR)


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
