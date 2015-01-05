import copy
import json
import re
import requests
import os
from multiprocessing.dummy import Pool

from django.conf import settings
from django.core.management.base import NoArgsCommand
from fle_utils.general import ensure_dir

logging = settings.LOG


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
        download_urls(image_urls)

def download_urls(urls):
    pool = Pool(5)
    pool.map(download_url_to_dir, urls)

def download_url_to_dir(url, dir=settings.CONTENT_ROOT):
    dir = os.path.join(dir, "khan")
    ensure_dir(dir)
    logging.info("downloading %s" % url)
    r = requests.get(url)
    try:
        r.raise_for_status()
    except Exception as e:
        logging.error(str(r))
        return None
    filename = os.path.basename(url)
    with open(os.path.join(dir, filename), 'w') as f:
        f.write(r.content)

# def download_url(url, fobject):
#     r = requests.get(url)
#     r.raise_for_status()
#     filename = os.path.basename(url)
#     fobject.writestr(filename.content)


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
        v['item_data'] = re.sub(url_to_replace, r'/content/khan/\g<filename>', old_item_data)

    return newitems
