import copy
import json
import os
import re
import requests
import tempfile
import zipfile
from multiprocessing.dummy import Pool as ThreadPool
from threading import Lock

from django.conf import settings as django_settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand

import kalite.version as version

from kalite.topic_tools import get_content_cache, get_exercise_cache
from kalite.contentload import settings

logging = django_settings.LOG

ZIP_FILE_PATH = os.path.join(django_settings.USER_DATA_ROOT, "assessment.zip")

IMAGE_URL_REGEX = re.compile('https?://[\w\.\-\/]+\/(?P<filename>[\w\.\-\%]+\.(png|gif|jpg|jpeg|svg))', flags=re.IGNORECASE)

WEB_GRAPHIE_URL_REGEX = re.compile('web\+graphie://ka\-perseus\-graphie\.s3\.amazonaws\.com\/(?P<filename>\w+)', flags=re.IGNORECASE)

IMAGE_URLS_NOT_TO_REPLACE = set([
    "http://www.dogs.com/photo.jpg",
    "https://www.kasandbox.org/programming-images/creatures/OhNoes.png",
])

# This is used for image URLs that don't end in an image extension, or are otherwise messed up.
# Here we can manually map such URLs to a nice, friendly filename that will get used in the assessment item data.
MANUAL_IMAGE_URL_TO_FILENAME_MAPPING = {
    "http://www.marineland.com/~/media/UPG/Marineland/Products/Glass%20Aquariums/Cube%20Aquariums/12268%20MCT45B%200509jpg49110640x640.ashx?w=300&h=300&bc=white": "aquarium.jpg",
    "https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcSbTT6DecPnyTp5t-Ar9bgQcwNxLV8F6dvSFDYHKZSs1JINCCRFJw": "ar9bgqcwnxlv8f6dvsfdyhkzss1jinccrfjw.jpg",
}

# this ugly regex looks for links to content on the KA site, also including the markdown link text and surrounding bold markers (*), e.g.
# **[Read this essay to review](https://www.khanacademy.org/humanities/art-history/art-history-400-1300-medieval---byzantine-eras/anglo-saxon-england/a/the-lindisfarne-gospels)**
# TODO(jamalex): answer any questions people might have when this breaks!
CONTENT_URL_REGEX_PLAIN = "https?://www\.khanacademy\.org/[\/\w\-\%]*/./(?P<slug>[\w\-]+)"
CONTENT_URL_REGEX = re.compile("(?P<prefix>)" + CONTENT_URL_REGEX_PLAIN + "(?P<suffix>)", flags=re.IGNORECASE)
CONTENT_LINK_REGEX = re.compile("(?P<prefix>\**\[[^\]\[]+\] ?\(?) ?" + CONTENT_URL_REGEX_PLAIN + "(?P<suffix>\)? ?\**)", flags=re.IGNORECASE)

ZIP_WRITE_MUTEX = Lock()


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        logging.info("fetching assessment items")

        # load the assessmentitems
        assessment_items = json.load(open(settings.KHAN_ASSESSMENT_ITEM_JSON_PATH))

        image_urls = find_all_image_urls(assessment_items)
        graphie_urls = find_all_graphie_urls(assessment_items)

        logging.info("rewriting urls")
        new_assessment_items = localize_all_image_urls(assessment_items)
        new_assessment_items = localize_all_content_links(new_assessment_items)
        new_assessment_items = localize_all_graphie_urls(new_assessment_items)

        # TODO(jamalex): We should migrate this away from direct-to-zip so that we can re-run it
        # without redownloading all files. Not possible currently because ZipFile has no `delete`.
        logging.info("downloading images")
        with open(ZIP_FILE_PATH, "w") as f:
            zf = zipfile.ZipFile(f, "w")  # zipfile.ZipFile isn't a context manager yet for python 2.6
            write_assessment_item_db_to_zip(zf, new_assessment_items)
            download_urls_to_zip(zf, image_urls)
            download_urls_to_zip(zf, graphie_urls)
            write_assessment_item_version_to_zip(zf)
            zf.close()

        logging.info("Zip File with images placed in %s" % ZIP_FILE_PATH)


def write_assessment_item_version_to_zip(zf, versionnumber=version.SHORTVERSION):
    zf.writestr("assessmentitems.version", versionnumber)


def write_assessment_item_db_to_zip(zf, assessment_items):
    temp_json_file = os.path.join(tempfile.gettempdir(), "assessmentitems.json")
    temp_database_file = os.path.join(tempfile.gettempdir(), "assessmentitems.sqlite")
    with open(temp_json_file, "w") as f:
        json.dump(assessment_items, f)
    call_command("init_assessment_items", assessment_items_filepath=temp_json_file, database_path=temp_database_file, bulk_create=True)
    with open(temp_database_file) as f:
        db_data = f.read()
    zf.writestr("assessmentitems.sqlite", db_data)


def download_urls_to_zip(zf, urls):

    urls = set(urls)

    pool = ThreadPool(10)
    download_to_zip_func = lambda url: download_url_to_zip(zf, url)
    pool.map(download_to_zip_func, urls)


def download_url_to_zip(zf, url):
    # use a manual mapping if available, otherwise get the filename from the end of the url
    filename = MANUAL_IMAGE_URL_TO_FILENAME_MAPPING.get(url, os.path.basename(url))
    filepath = _get_subpath_from_filename(filename)
    try:
        url = url.replace("https://ka-", "http://ka-")
        filecontent = fetch_file_from_url_or_cache(url)
    except Exception as e:
        # we don't want a failed image request to download, but we
        # want to inform the user of the error
        logging.error("Error when downloading from URL: %s (%s)" % (url, e))
        return

    # Without a mutex, the generated zip files were corrupted when writing with concurrency > 1
    with ZIP_WRITE_MUTEX:
        zf.writestr(filepath, filecontent)


def fetch_file_from_url_or_cache(url):
    # use a manual mapping if available, otherwise get the filename from the end of the url
    filename = MANUAL_IMAGE_URL_TO_FILENAME_MAPPING.get(url, os.path.basename(url))
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


def find_all_image_urls(items):

    for url in MANUAL_IMAGE_URL_TO_FILENAME_MAPPING:
        yield url

    for v in items.itervalues():
        for match in re.finditer(IMAGE_URL_REGEX, v["item_data"]):
            if match.group(0) not in IMAGE_URLS_NOT_TO_REPLACE:
                yield str(match.group(0))  # match.group(0) means get the entire string


def localize_all_image_urls(items):
    # we copy so we make sure we don't modify the items passed in to this function
    newitems = copy.deepcopy(items)

    for item in newitems.itervalues():
        item['item_data'] = localize_image_urls(item['item_data'])

    return newitems


def localize_image_urls(item_data):
    for url, filename in MANUAL_IMAGE_URL_TO_FILENAME_MAPPING.items():
        item_data = item_data.replace(url, _get_path_from_filename(filename))
    item_data = re.sub(IMAGE_URL_REGEX, _old_image_url_to_content_url, item_data)
    return item_data


def find_all_graphie_urls(items):

    for v in items.itervalues():
        for match in re.finditer(WEB_GRAPHIE_URL_REGEX, v["item_data"]):
            base_filename = str(match.group(0)).replace("web+graphie:", "https:") # match.group(0) means get the entire string
            yield base_filename + ".svg"
            yield base_filename + "-data.json"


def localize_all_graphie_urls(items):
    # we copy so we make sure we don't modify the items passed in to this function
    newitems = copy.deepcopy(items)

    for item in newitems.itervalues():
        item['item_data'] = localize_graphie_urls(item['item_data'])

    return newitems


def localize_graphie_urls(item_data):

    return re.sub(WEB_GRAPHIE_URL_REGEX, _old_graphie_url_to_content_url, item_data)


def convert_urls(item_data):
    """Convert urls in i18n strings into localhost urls.
    This function is used by ka-lite-central/centralserver/i18n/management/commands/update_language_packs.py"""
    item_data = localize_image_urls(item_data)
    item_data = localize_content_links(item_data)
    item_data = localize_graphie_urls(item_data)
    return item_data


def _old_graphie_url_to_content_url(matchobj):
    return "web+graphie:" + _get_path_from_filename(matchobj.group("filename"))


def _old_image_url_to_content_url(matchobj):
    url = matchobj.group(0)
    if url in IMAGE_URLS_NOT_TO_REPLACE:
        return url
    return _get_path_from_filename(matchobj.group("filename"))


def _get_path_from_filename(filename):
    return "/content/khan/" + _get_subpath_from_filename(filename)


def _get_subpath_from_filename(filename):
    filename = filename.replace("%20", "_")
    return "%s/%s" % (filename[0:3], filename)


def localize_all_content_links(items):
    # we copy so we make sure we don't modify the items passed in to this function
    newitems = copy.deepcopy(items)

    # loop over every item, and replace links in them to point to local resources, if available
    for item in newitems.itervalues():
        item['item_data'] = localize_content_links(item['item_data'])

    return newitems


def localize_content_links(item_data):
    item_data = re.sub(CONTENT_LINK_REGEX, _old_content_links_to_local_links, item_data)
    item_data = re.sub(CONTENT_URL_REGEX, _old_content_links_to_local_links, item_data)
    return item_data


def _old_content_links_to_local_links(matchobj):
    # replace links in them to point to local resources, if available, otherwise return an empty string
    content = _get_content_by_readable_id(matchobj.group("slug"))
    url = matchobj.group(0)
    if not content or "path" not in content:
        if "/a/" not in url and "/p/" not in url:
            print "Content link target not found:", url
        return ""

    return "%s/learn/%s%s" % (matchobj.group("prefix"), content["path"], matchobj.group("suffix"))


CONTENT_BY_READABLE_ID = None
def _get_content_by_readable_id(readable_id):
    global CONTENT_BY_READABLE_ID
    if not CONTENT_BY_READABLE_ID:
        CONTENT_BY_READABLE_ID = dict([(c["readable_id"], c) for c in get_content_cache().values()])
    try:
        return CONTENT_BY_READABLE_ID[readable_id]
    except KeyError:
        return CONTENT_BY_READABLE_ID.get(re.sub("\-+", "-", readable_id).lower(), None)


def _list_all_exercises_with_bad_links():
    """This is a standalone helper method used to provide KA with a list of exercises with bad URLs in them."""
    url_pattern = r"https?://www\.khanacademy\.org/[\/\w\-]*/./(?P<slug>[\w\-]+)"
    assessment_items = json.load(open(settings.KHAN_ASSESSMENT_ITEM_JSON_PATH))
    for ex in get_exercise_cache().values():
        checked_urls = []
        displayed_title = False
        for aidict in ex.get("all_assessment_items", []):
            ai = assessment_items[aidict["id"]]
            for match in re.finditer(url_pattern, ai["item_data"], flags=re.IGNORECASE):
                url = str(match.group(0))
                if url in checked_urls:
                    continue
                checked_urls.append(url)
                status_code = requests.get(url).status_code
                if status_code != 200:
                    if not displayed_title:
                        print "EXERCISE: '%s'" % ex["title"], ex["path"]
                        displayed_title = True
                    print "\t", status_code, url

