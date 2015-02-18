import StringIO
import json
import requests
import os
import urlparse
import zipfile
from distutils.version import StrictVersion
from fle_utils.general import ensure_dir
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logging = settings.LOG

from kalite import version

KHAN_DATA_PATH = os.path.join(
    settings.CONTENT_DATA_PATH,
    "khan",
)

KHAN_CONTENT_PATH = os.path.join(
    settings.CONTENT_ROOT,
    "khan"
)

ASSESSMENT_ITEMS_PATH = os.path.join(KHAN_DATA_PATH, "assessmentitems.json")
ASSESSMENT_ITEMS_VERSION_PATH = os.path.join(KHAN_DATA_PATH, "assessmentitems.json.version")

logging = settings.LOG

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-f", "--force",
                    action="store_true",
                    dest="force_download",
                    default=False,
                    help="If specified, force the download even if our assessment items is up-to-date."),
    )

    def handle(self, *args, **kwargs):
        if len(args) != 1:
            raise CommandError("We expect only one argument; the location of the zip.")

        ziplocation = args[0]

        if not should_upgrade_assessment_items() and not kwargs['force_download']:
            logging.debug("Assessment item resources are in the right version. Skipping download;")
            return

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


def should_upgrade_assessment_items():
    # if assessmentitems.json.version doesn't exist, then we assume
    # that they haven't got assessment items EVER
    if not os.path.exists(ASSESSMENT_ITEMS_VERSION_PATH):
        logging.debug("%s does not exist; downloading assessment items" % ASSESSMENT_ITEMS_VERSION_PATH)
        return True

    with open(ASSESSMENT_ITEMS_VERSION_PATH) as f:
        assessment_items_version = StrictVersion(f.read())

    software_version = StrictVersion(version.SHORTVERSION)
    return software_version > assessment_items_version


def extract_assessment_items_to_data_dir(zf):
    zf.extract("assessmentitems.json", KHAN_DATA_PATH)
    zf.extract("assessmentitems.json.version", KHAN_DATA_PATH)


def unpack_zipfile_to_khan_content(zf):
    dir = settings.ASSESSMENT_ITEMS_RESOURCES_DIR
    ensure_dir(dir)
    zf.extractall(dir)


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
