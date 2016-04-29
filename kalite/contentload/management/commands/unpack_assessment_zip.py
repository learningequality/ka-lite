import requests
import os
import urlparse
import zipfile
import tempfile
import sys
import shutil
import threading
import time
from distutils.version import StrictVersion
from fle_utils.general import ensure_dir
from optparse import make_option

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

logging = django_settings.LOG

from kalite import version
from kalite.contentload import settings


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
            logging.debug("Assessment item resources are in the right version. Doing nothing.")
            return

        if is_valid_url(ziplocation):  # url; download the zip
            logging.info("Downloading assessment item data from a remote server. Please be patient; this file is big, so this may take some time...")
            # this way we can download stuff larger than the device's RAM
            r = requests.get(ziplocation, prefetch=False)
            content_length = r.headers.get("Content-Length")
            logging.info("Downloaded size: ", str(int(content_length) // 1024 // 1024) + " MB" if content_length else "Unknown")
            sys.stdout.write("Downloading file...")
            sys.stdout.flush()
            f = tempfile.TemporaryFile("r+")
            r.raise_for_status()
            for cnt, chunk in enumerate(r.iter_content(chunk_size=1024)):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    if cnt % 1000 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    f.flush()
            f.seek(0)
            sys.stdout.write("\n")
        else:                   # file; just open it normally
            f = open(ziplocation, "rb")

        def unpack():
            zf = zipfile.ZipFile(f, "r")
            unpack_zipfile_to_content_folder(zf)

        unpack_thread = threading.Thread(target=unpack)
        unpack_thread.daemon = True
        unpack_thread.start()
        while unpack_thread.is_alive():
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
        unpack_thread.join()

        logging.info("Scanning items and updating content db...")
        call_command("annotate_content_items")
        logging.info("Done, assessment items installed and everything updated. Refresh your browser!")


# TODO(jamalex): move this to somewhere outside of this management command file, as we're importing it elsewhere
def should_upgrade_assessment_items():
    # if assessmentitems.version doesn't exist, then we assume
    # that they haven't got assessment items EVER
    if not os.path.exists(settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH):
        logging.debug("%s does not exist; downloading assessment items" % settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH)
        return True

    with open(settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH) as f:
        assessment_items_version = StrictVersion(f.read())

    software_version = StrictVersion(version.SHORTVERSION)
    return software_version > assessment_items_version


def unpack_zipfile_to_content_folder(zf):
    try:
        channel = zf.read("channel.name")
        folder = os.path.join(settings.ASSESSMENT_ITEM_ROOT, channel)
    except KeyError:
        # 0.16 legacy assessment zip no longer comes with a channel.name file
        folder = settings.KHAN_ASSESSMENT_ITEM_ROOT

    logging.info("Unpacking to folder {}...".format(folder))

    ensure_dir(folder)
    zf.extractall(folder)

    # If assessmentitems.version exists, copy it to another location outside
    # of the channel folder because for some reason a test expects it to be
    # there.
    version_file = os.path.join(folder, 'assessmentitems.version')
    version_file_copied_dest = os.path.join(
        settings.ASSESSMENT_ITEM_ROOT,
        'assessmentitems.version'
    )
    if version_file_copied_dest != version_file:
        if os.path.isfile(version_file_copied_dest):
            os.unlink(version_file_copied_dest)
        # Test that file exists because there's a test that mocks unzipping and
        # then this would fail because a file that should exist doesn't (doh)
        if os.path.isfile(version_file):
            # Ensure that special files are in their configured locations
            shutil.copy(
                version_file,
                version_file_copied_dest
            )


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    allowed_methods = ("http", "https")  # urlparse("C:\folder") results in scheme = "c", so use a whitelist
    return bool(parsed_url.scheme in allowed_methods)
