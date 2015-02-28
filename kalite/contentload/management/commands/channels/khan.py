import base
import os
import json
import requests
import threading
import time

from collections_local_copy import OrderedDict
from fle_utils.general import ensure_dir
from functools import partial
from khan_api_python.api_models import Khan, APIError
from multiprocessing.dummy import Pool as ThreadPool

from django.conf import settings

from kalite.updates.videos import REMOTE_VIDEO_SIZE_FILEPATH

logging = settings.LOG

slug_key = {
    "Topic": "node_slug",
    "Video": "readable_id",
    "Exercise": "name",
    "AssessmentItem": "id",
}

title_key = {
    "Topic": "title",
    "Video": "title",
    "Exercise": "display_name",
    "AssessmentItem": "name"
}

id_key = {
    "Topic": "node_slug",
    "Video": "youtube_id",
    "Exercise": "name",
    "AssessmentItem": "id"
}

iconfilepath = "/images/power-mode/badges/"
iconextension = "-40x40.png"
defaulticon = "default"

attribute_whitelists = {
    "Topic": ["kind", "hide", "description", "id", "topic_page_url", "title", "extended_slug", "children", "node_slug", "in_knowledge_map", "icon_src", "child_data", "render_type", "path", "slug"],
    "Video": ["kind", "description", "title", "duration", "keywords", "youtube_id", "download_urls", "readable_id", "in_knowledge_map", "path", "slug", "format"],
    "Exercise": ["kind", "description", "related_video_readable_ids", "display_name", "live", "name", "seconds_per_fast_problem", "prerequisites", "all_assessment_items", "uses_assessment_items", "path", "slug"],
    "AssessmentItem": ["kind", "name", "item_data", "author_names", "sha", "id"]
}

denormed_attribute_list = {
    "Video": ["kind", "description", "title", "id", "slug", "path"],
    "Exercise": ["kind", "description", "title", "id", "slug", "path"]
}

kind_blacklist = [None, "Separator", "CustomStack", "Scratchpad", "Article"]

slug_blacklist = ["new-and-noteworthy", "talks-and-interviews", "coach-res"] # not relevant
slug_blacklist += ["cs", "towers-of-hanoi"] # not (yet) compatible
slug_blacklist += ["cc-third-grade-math", "cc-fourth-grade-math", "cc-fifth-grade-math", "cc-sixth-grade-math", "cc-seventh-grade-math", "cc-eighth-grade-math"] # common core
slug_blacklist += ["MoMA", "getty-museum", "stanford-medicine", "crash-course1", "mit-k12", "hour-of-code", "metropolitan-museum", "bitcoin", "tate", "crash-course1", "crash-course-bio-ecology", "british-museum", "aspeninstitute", "asian-art-museum", "amnh"] # partner content

# TODO(jamalex): re-check these videos later and remove them from here if they've recovered
slug_blacklist += ["mortgage-interest-rates", "factor-polynomials-using-the-gcf", "inflation-overview", "time-value-of-money", "changing-a-mixed-number-to-an-improper-fraction", "applying-the-metric-system"] # errors on video downloads
# 'Mortgage interest rates' at http://s3.amazonaws.com/KA-youtube-converted/vy_pvstdBhg.mp4/vy_pvstdBhg.mp4...
# 'Inflation overview' at http://s3.amazonaws.com/KA-youtube-converted/-Z5kkfrEc8I.mp4/-Z5kkfrEc8I.mp4...
# 'Factor expressions using the GCF' at http://s3.amazonaws.com/KA-youtube-converted/_sIuZHYrdWM.mp4/_sIuZHYrdWM.mp4...
# 'Time value of money' at http://s3.amazonaws.com/KA-youtube-converted/733mgqrzNKs.mp4/733mgqrzNKs.mp4...
# 'Applying the metric system' at http://s3.amazonaws.com/KA-youtube-converted/CDvPPsB3nEM.mp4/CDvPPsB3nEM.mp4...
# 'Mixed numbers: changing to improper fractions' at http://s3.amazonaws.com/KA-youtube-converted/xkg7370cpjs.mp4/xkg7370cpjs.mp4...

# Attributes that are OK for a while, but need to be scrubbed off by the end.
temp_ok_atts = ["x_pos", "y_pos", "icon_src", u'topic_page_url', u'hide', "live", "node_slug", "extended_slug"]

channel_data = {
    "slug_key": slug_key,
    "title_key": title_key,
    "id_key": id_key,
    "iconfilepath": iconfilepath,
    "iconextension":  iconextension,
    "defaulticon": defaulticon,
    "attribute_whitelists": attribute_whitelists,
    "denormed_attribute_list": denormed_attribute_list,
    "kind_blacklist": kind_blacklist,
    "slug_blacklist": slug_blacklist,
    "temp_ok_atts": temp_ok_atts,
    "require_download_link": True,
}

whitewash_node_data = partial(base.whitewash_node_data, channel_data=channel_data)

def denorm_data(node):
    if node:
        kind = node.get("kind", "")
        if channel_data["denormed_attribute_list"].has_key(kind):
            for key in node.keys():
                if key not in channel_data["denormed_attribute_list"][kind] or not node.get(key, "") or isinstance(node.get(key), partial):
                    del node[key]


def build_full_cache(items, id_key="id"):
    """
    Uses list of items retrieved from Khan Academy API to
    create an item cache with fleshed out meta-data.
    """

    output = {}

    for item in items:
        for attribute in item._API_attributes:
            logging.info("Fetching item information for {id}, attribute: {attribute}".format(id=item.get(id_key, "Unknown"), attribute=attribute))
            try:
                dummy_variable_to_force_fetch = item.__getattr__(attribute)
                if isinstance(item[attribute], list):
                    for subitem in item[attribute]:
                        if isinstance(subitem, dict):
                            try:
                                subitem = json.loads(subitem.toJSON())
                            except AttributeError:
                                pass
                            if subitem.has_key("kind"):
                                subitem = whitewash_node_data(
                                    {key: value for key, value in subitem.items()})
                                denorm_data(subitem)
                elif isinstance(item[attribute], dict):
                    try:
                        item[attribute] = json.loads(item[attribute].toJSON())
                    except AttributeError:
                        pass
                    if item[attribute].has_key("kind"):
                        item[attribute] = whitewash_node_data(
                            {key: value for key, value in item.attribute.items()})
                        denorm_data(item[attribute])
            except APIError as e:
                del item[attribute]
        try:
            item = json.loads(item.toJSON())
        except AttributeError:
            logging.error("Unable to serialize %r" % item)

        output[item["id"]] = whitewash_node_data(item)

    return output

def retrieve_API_data(channel=None):

    # TODO(jamalex): See how much of what we do here can be replaced by KA's new projection-based API
    # http://www.khanacademy.org/api/v2/topics/topictree?projection={"topics":[{"slug":1,"childData":[{"id":1}]}]}

    khan = Khan()

    logging.info("Fetching Khan topic tree")

    topic_tree = khan.get_topic_tree()

    logging.info("Fetching Khan exercises")

    exercises = khan.get_exercises()

    exercises_dummy = khan.get_exercises()

    logging.info("Fetching Khan videos")

    content = khan.get_videos()

    # Hack to hardcode the mp4 format flag on Videos.
    for con in content:
        con["format"] = "mp4"

    # Compute and save file sizes
    logging.info("Checking remote content file sizes...")
    try:
        with open(REMOTE_VIDEO_SIZE_FILEPATH, "r") as fp:
            old_sizes = json.load(fp)
    except:
        old_sizes = {}
    blacklist = [key for key, val in old_sizes.items() if val > 0] # exclude any we already know about
    sizes_by_id, sizes = query_remote_content_file_sizes(content, blacklist=blacklist)
    ensure_dir(os.path.dirname(REMOTE_VIDEO_SIZE_FILEPATH))
    old_sizes.update(sizes_by_id)
    sizes = OrderedDict(sorted(old_sizes.items()))
    with open(REMOTE_VIDEO_SIZE_FILEPATH, "w") as fp:
        json.dump(sizes, fp, indent=2)
    logging.info("Finished checking remote content file sizes...")

    assessment_items = []

    # Limit number of simultaneous requests
    semaphore = threading.BoundedSemaphore(100)

    def fetch_assessment_data(exercise):
        logging.info("Fetching Assessment Item Data for {exercise}".format(exercise=exercise.display_name))
        for assessment_item in exercise.all_assessment_items:
            counter = 0
            wait = 5
            while wait:
                try:
                    semaphore.acquire()
                    logging.info("Fetching assessment item {assessment}".format(assessment=assessment_item["id"]))
                    assessment_data = khan.get_assessment_item(assessment_item["id"])
                    semaphore.release()
                    if assessment_data.get("item_data"):
                        wait = 0
                        assessment_items.append(assessment_data)
                    else:
                        logging.info("Fetching assessment item {assessment} failed retrying in {wait}".format(assessment=assessment_item["id"], wait=wait))
                        time.sleep(wait)
                        wait = wait*2
                        counter += 1
                except (requests.ConnectionError, requests.Timeout):
                    semaphore.release()
                    time.sleep(wait)
                    wait = wait*2
                    counter += 1
                if counter > 5:
                    logging.info("Fetching assessment item {assessment} failed more than 5 times, aborting".format(assessment=assessment_item["id"]))
                    break

    threads = [threading.Thread(target=fetch_assessment_data, args=(exercise,)) for exercise in exercises_dummy]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return topic_tree, exercises, assessment_items, content

def query_remote_content_file_sizes(content_items, threads=10, blacklist=[]):
    """
    Query and store the file sizes for downloadable videos, by running HEAD requests against them,
    and reading the `content-length` header. Right now, this is only for the "khan" channel, and hence lives here.
    TODO(jamalex): Generalize this to other channels once they're centrally hosted and downloadable.
    """
    sizes_by_id = {}

    if isinstance(content_items, dict):
        content_items = content_items.values()

    content_items = [content for content in content_items if content["format"] in content.get("download_urls", {}) and content["youtube_id"] not in blacklist]

    pool = ThreadPool(threads)
    sizes = pool.map(get_content_length, content_items)

    for content, size in zip(content_items, sizes):
        # TODO(jamalex): This should be generalized from "youtube_id" to support other content types
        if size:
            sizes_by_id[content["youtube_id"]] = size

    return sizes_by_id, sizes


def get_content_length(content):
    url = content["download_urls"][content["format"]].replace("http://fastly.kastatic.org/", "http://s3.amazonaws.com/") # because fastly is SLOWLY
    logging.info("Checking remote file size for content '{title}' at {url}...".format(title=content.get("title"), url=url))
    size = 0
    for i in range(5):
        try:
            size = int(requests.head(url, timeout=60).headers["content-length"])
            break
        except requests.Timeout:
            logging.warning("Timed out on try {i} while checking remote file size for '{title}'!".format(title=content.get("title"), i=i))
        except TypeError:
            logging.warning("No numeric content-length returned while checking remote file size for '{title}' ({readable_id})!".format(**content))
            break
    if size:
        logging.info("Finished checking remote file size for content '{title}'!".format(title=content.get("title")))
    else:
        logging.error("No file size retrieved (timeouts?) for content '{title}'!".format(title=content.get("title")))
    return size


rebuild_topictree = partial(base.rebuild_topictree, whitewash_node_data=whitewash_node_data, retrieve_API_data=retrieve_API_data, channel_data=channel_data)
