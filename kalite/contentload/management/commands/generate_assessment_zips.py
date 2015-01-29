import copy
import json
import os
import re
import requests
import tempfile
import zipfile
from multiprocessing.dummy import Pool as ThreadPool

from django.conf import settings
from django.core.management.base import NoArgsCommand

logging = settings.LOG

ZIP_FILE_PATH = os.path.join(settings.PROJECT_PATH, "assessment_item_resources.zip")


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        logging.info("fetching assessment items")

        # load the assessmentitems
        assessment_items = json.load(open(os.path.join(settings.PROJECT_PATH, "..", "data", "khan", "assessmentitems.json")))

        image_urls = all_image_urls(assessment_items)

        logging.info("rewriting image urls")
        new_assessment_items = localhosted_image_urls(assessment_items)

        # TODO(jamalex): We should migrate this away from direct-to-zip so that we can re-run it
        # without redownloading all files. Not possible currently because ZipFile has no `delete`.
        logging.info("downloading images")
        with zipfile.ZipFile(ZIP_FILE_PATH, "w") as zf:
            write_assessment_to_zip(zf, new_assessment_items)
            zip_file_path = download_urls(zf, image_urls)

        logging.info("Zip File with images placed in %s" % zip_file_path)


def write_assessment_to_zip(zf, assessment_items):
    assessment_json_string = json.dumps(assessment_items)
    zf.writestr("assessmentitems.json", assessment_json_string)


def download_urls(zf, urls):

    urls = set(urls)

    pool = ThreadPool(5)
    download_to_zip_func = lambda url: download_url_to_zip(zf, url)
    map(download_to_zip_func, urls)

    return ZIP_FILE_PATH


def download_url_to_zip(zipfile, url):
    url = url.replace("https://ka-", "http://ka-")
    filename = os.path.basename(url)
    try:
        filecontent = fetch_file_from_url_or_cache(url)
    except Exception as e:
        # we don't want a failed image request to download, but we
        # want to inform the user of the error
        logging.error("Error when downloading from URL: %s (%s)" % (url, e))
        return

    zipfile.writestr(filename, filecontent)


def fetch_file_from_url_or_cache(url):
    filename = os.path.basename(url)
    cached_file_path = os.path.join(tempfile.gettempdir(), filename)

    if os.path.exists(cached_file_path):  # just read from the cache file
        logging.info("reading cached file %s" % cached_file_path)
        with open(cached_file_path) as f:
            out = f.read()
    else:                       # fetch, then write to the cache file
        logging.info("downloading file %s" % url)
        r = requests.get(url)
        r.raise_for_status()
        with open(cached_file_path, "w") as f:
            f.write(r.content)
        out = r.content

    return out


def all_image_urls(items):
    for _, v in items.iteritems():

        item_data = v["item_data"]
        imgurlregex = r"https?://[\w\.\-\/]+\/(?P<filename>[\w\.\-]+\.(png|gif|jpg))"

        for match in re.finditer(imgurlregex, item_data):
            yield str(match.group(0))  # match.group(0) means get the entire string


def localhosted_image_urls(items):
    newitems = copy.deepcopy(items)

    url_to_replace = r'https?://[\w\.\-\/]+\/(?P<filename>[\w\.\-]+\.(png|gif|jpg))'

    for _, v in newitems.iteritems():
        old_item_data = v['item_data']
        v['item_data'] = re.sub(url_to_replace, _old_item_url_to_content_url, old_item_data)

    return newitems


def _old_item_url_to_content_url(matchobj):
    return "/content/khan/%s" % matchobj.group("filename")
