import copy
import json
import re
import requests
import os
import zipfile
from multiprocessing.dummy import Pool as ThreadPool

from django.conf import settings
from django.core.management.base import NoArgsCommand

logging = settings.LOG

ZIP_FILE_PATH = os.path.join(settings.PROJECT_PATH, "assessment_item_resources.zip")


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        logging.info("fetching assessment items")
        assessment_items_url = "https://s3.amazonaws.com/uploads.hipchat.com/86198%2F624195%2FtYo7Ez0tt3e1qQW%2Fassessmentitems.json"

        # cache the assessmentitems
        assessment_items_cache_path = os.path.join(settings.PROJECT_PATH, "assessmentitems.cache.json")
        if os.path.isfile(assessment_items_cache_path):
            assessment_items = json.load(open(assessment_items_cache_path))
        else:
            assessment_items = json.loads(requests.get(assessment_items_url).content)
            json.dump(assessment_items, open(assessment_items_cache_path, "w"))

        image_urls = all_image_urls(assessment_items)

        logging.info("rewriting image urls")
        new_assessment_items = localhosted_image_urls(assessment_items)

        with open(os.path.join(settings.PROJECT_PATH, "..", "data", "khan", "assessmentitems.json"), "w") as f:
            json.dump(new_assessment_items, f, indent=4)

        logging.info("downloading images")
        with zipfile.ZipFile(ZIP_FILE_PATH, "w") as zf:
            write_assessment_to_zip(zf, new_assessment_items)
            zip_file_path = download_urls(zf, image_urls)

        logging.info("Zip File with images placed in %s" % zip_file_path)


def write_assessment_to_zip(zf, assessment_items):
    assessment_json_string = json.dumps(assessment_items)
    zf.writestr("assessment_items.json", assessment_json_string)


def download_urls(zf, urls):
    pool = ThreadPool(5)
    download_to_zip_func = lambda url: download_url_to_zip(zf, url)
    pool.map(download_to_zip_func, urls)

    return ZIP_FILE_PATH


def download_url_to_zip(zipfile, url):
    logging.info("downloading %s" % url)
    filename = os.path.basename(url)
    r = requests.get(url)
    try:
        r.raise_for_status()
    except Exception as e:
        logging.error(str(r))
        return None
    zipfile.writestr(filename, r.content)


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
