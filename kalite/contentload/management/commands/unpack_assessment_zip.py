import requests
import os
import urlparse
import zipfile
import tempfile
import sys
from distutils.version import StrictVersion
from fle_utils.general import ensure_dir
from optparse import make_option

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError

logging = django_settings.LOG

from kalite import version
from kalite.contentload import settings

logging = django_settings.LOG

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
            print "Downloading assessment item data from a remote server. Please be patient; this file is big, so this may take some time..."
            # this way we can download stuff larger than the device's RAM
            r = requests.get(ziplocation, prefetch=False)
            content_length = r.headers.get("Content-Length")
            print "Downloaded size: ", str(int(content_length) // 1024 // 1024) + " MB" if content_length else "Unknown"
            sys.stdout.write("Downloading file...")
            sys.stdout.flush()
            f = tempfile.TemporaryFile("r+")
            r.raise_for_status()
            for cnt, chunk in enumerate(r.iter_content(chunk_size=1024)):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    if cnt % 1000 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                    f.flush()
            f.seek(0)
            sys.stdout.write("\n")
        else:                   # file; just open it normally
            f = open(ziplocation, "rb")

        print "Unpacking..."
        zf = zipfile.ZipFile(f, "r")
        unpack_zipfile_to_khan_content(zf)


def should_upgrade_assessment_items():
    # if assessmentitems.version doesn't exist, then we assume
    # that they haven't got assessment items EVER
    if not os.path.exists(django_settings.KHAN_ASSESSMENT_ITEM_DATABASE_PATH) or not os.path.exists(django_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH):
        logging.debug("%s does not exist; downloading assessment items" % django_settings.KHAN_ASSESSMENT_ITEM_DATABASE_PATH)
        return True

    with open(django_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH) as f:
        assessment_items_version = StrictVersion(f.read())

    software_version = StrictVersion(version.SHORTVERSION)
    return software_version > assessment_items_version


def unpack_zipfile_to_khan_content(zf):
    folder = settings.KHAN_CONTENT_PATH
    ensure_dir(folder)
    zf.extractall(folder)
    # Move the version file to configured location
    file(django_settings.KHAN_ASSESSMENT_ITEM_VERSION_PATH, 'w').write(
        open(
            os.path.join(settings.KHAN_CONTENT_PATH, 'assessmentitems.version'),
            'r'
        ).read(),
    )
    file(django_settings.KHAN_ASSESSMENT_ITEM_DATABASE_PATH, 'w').write(
        open(
            os.path.join(settings.KHAN_CONTENT_PATH, 'assessmentitems.sqlite'),
            'r'
        ).read(),
    )


def is_valid_url(url):
    parsed_url = urlparse.urlparse(url)
    return bool(parsed_url.scheme)
