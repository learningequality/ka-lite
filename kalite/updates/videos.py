"""
"""
import os

from django.conf import settings; logging = settings.LOG

from fle_utils import videos  # keep access to all functions
from fle_utils.general import softload_json
from fle_utils.videos import *  # get all into the current namespace, override some.
from kalite.i18n import get_srt_path, get_srt_url, get_id2oklang_map, get_youtube_id, get_langs_with_subtitle
from kalite.main.topic_tools import get_topic_tree, get_videos


REMOTE_VIDEO_SIZE_FILEPATH = os.path.join(settings.DATA_PATH, "content", "video_file_sizes.json")
AVERAGE_VIDEO_SIZE = 14000000

REMOTE_VIDEO_SIZES = None
def get_remote_video_size(youtube_id, default=AVERAGE_VIDEO_SIZE, force=False):
    global REMOTE_VIDEO_SIZES
    if REMOTE_VIDEO_SIZES is None:
        REMOTE_VIDEO_SIZES = softload_json(REMOTE_VIDEO_SIZE_FILEPATH, logger=logging.debug)
    return REMOTE_VIDEO_SIZES.get(youtube_id, default)

def get_all_remote_video_sizes():
    global REMOTE_VIDEO_SIZES
    if REMOTE_VIDEO_SIZES is None:
        REMOTE_VIDEO_SIZES = softload_json(REMOTE_VIDEO_SIZE_FILEPATH, logger=logging.debug)
    return REMOTE_VIDEO_SIZES

def get_local_video_size(youtube_id, default=None):
    try:
        return os.path.getsize(os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id))
    except Exception as e:
        logging.debug(str(e))
        return default


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"
    return videos.download_video(youtube_id, settings.CONTENT_ROOT, download_url, format, callback)


def get_downloaded_youtube_ids(videos_path=None, format="mp4"):
    videos_path = videos_path or settings.CONTENT_ROOT
    return [path.split("/")[-1].split(".")[0] for path in glob.glob(os.path.join(videos_path, "*.%s" % format))]


def delete_downloaded_files(youtube_id):
    return videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)


def is_video_on_disk(youtube_id, format="mp4", videos_path=None):
    videos_path = videos_path or settings.CONTENT_ROOT
    video_file = os.path.join(videos_path, youtube_id + ".%s" % format)
    return os.path.isfile(video_file)


_vid_last_updated = 0
_vid_last_count = 0
def do_video_counts_need_update_question_mark(videos_path=None, format="mp4"):
    """
    Compare current state to global state variables to check whether video counts need updating.
    """
    global _vid_last_count
    global _vid_last_updated

    videos_path = videos_path or settings.CONTENT_ROOT
    if not os.path.exists(videos_path):
        return False

    files = glob.glob(os.path.join(videos_path, "*.%s" % format))

    # Have to update count and last_updated together, to make sure that next round
    #   stores all proper data (if something changed), or to do both checks (in case nothing changed)
    vid_count = len(files)
    if vid_count:
        vid_last_updated = os.path.getmtime(sorted(files, key=os.path.getmtime, reverse=True)[0])
    else:
        vid_last_updated = 0

    need_update = (vid_count != _vid_last_count) or (vid_last_updated != _vid_last_updated)

    _vid_last_count = vid_count
    _vid_last_updated = vid_last_updated

    return need_update


def stamp_availability_on_video(video, format="mp4", force=False, stamp_urls=True, videos_path=None):
    """
    Stamp all relevant urls and availability onto a video object (if necessary), including:
    * whether the video is available (on disk or online)
    """
    videos_path = videos_path or settings.CONTENT_ROOT

    def compute_video_availability(youtube_id, format, videos_path=videos_path):
        return {"on_disk": is_video_on_disk(youtube_id, format, videos_path=videos_path)}

    def compute_video_metadata(youtube_id, format):
        return {"stream_type": "video/%s" % format}

    def compute_video_urls(youtube_id, format, lang_code, on_disk=None, thumb_format="png", videos_path=videos_path):
        if on_disk is None:
            on_disk = is_video_on_disk(youtube_id, format, videos_path=videos_path)

        if on_disk:
            video_base_url = settings.CONTENT_URL + youtube_id
            stream_url = video_base_url + ".%s" % format
            thumbnail_url = video_base_url + ".png"
        elif settings.BACKUP_VIDEO_SOURCE and lang_code == "en":
            dict_vals = {"youtube_id": youtube_id, "video_format": format, "thumb_format": thumb_format }
            stream_url = settings.BACKUP_VIDEO_SOURCE % dict_vals
            thumbnail_url = settings.BACKUP_THUMBNAIL_SOURCE % dict_vals if settings.BACKUP_THUMBNAIL_SOURCE else None
        else:
            return {}  # no URLs
        return {"stream": stream_url, "thumbnail": thumbnail_url}

    video_availability = video.get("availability", {}) if not force else {}
    en_youtube_id = get_youtube_id(video["id"], None)
    video_map = get_id2oklang_map(video["id"]) or {}

    if not "on_disk" in video_availability:
        for lang_code in video_map.keys():
            youtube_id = video_map[lang_code].encode('utf-8')
            video_availability[lang_code] = compute_video_availability(youtube_id, format=format, videos_path=videos_path)
        video_availability["en"] = video_availability.get("en", {"on_disk": False})  # en should always be defined

        # Summarize status
        any_on_disk = any([lang_avail["on_disk"] for lang_avail in video_availability.values()])
        any_available = any_on_disk or bool(settings.BACKUP_VIDEO_SOURCE)

    if stamp_urls:
        # Loop over all known dubbed videos
        for lang_code, youtube_id in video_map.iteritems():
            urls = compute_video_urls(youtube_id, format, lang_code, on_disk=video_availability[lang_code]["on_disk"], videos_path=videos_path)
            if urls:
                # Only add properties if anything is available.
                video_availability[lang_code].update(urls)
                video_availability[lang_code].update(compute_video_metadata(youtube_id, format))

        # Get the (english) subtitle urls
        subtitle_lang_codes = get_langs_with_subtitle(en_youtube_id)
        subtitles_tuple = [(lc, get_srt_url(en_youtube_id, lc)) for lc in subtitle_lang_codes if os.path.exists(get_srt_path(lc, en_youtube_id))]
        subtitles_urls = dict(subtitles_tuple)
        video_availability["en"]["subtitles"] = subtitles_urls

    # now scrub any values that don't actually exist
    for lang_code in video_availability.keys():
        if not video_availability[lang_code]["on_disk"] and len(video_availability[lang_code]) == 1:
            del video_availability[lang_code]

    # Now summarize some availability onto the video itself
    video["availability"] = video_availability
    video["on_disk"]   = any_on_disk
    video["available"] = any_available

    return video


def stamp_availability_on_topic(topic, videos_path=None, force=True, stamp_urls=True, update_counts_question_mark= None):
    """ Uses the (json) topic tree to query the django database for which video files exist

    Returns the original topic dictionary, with two properties added to each NON-LEAF node:
      * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan Academy library)
      * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
    And the following property for leaf nodes:
      * on_disk

    Input Parameters:
    * videos_path: the path to video files
    """
    videos_path = videos_path or settings.CONTENT_ROOT
    if update_counts_question_mark is None:
        update_counts_question_mark = do_video_counts_need_update_question_mark()


    if not force and "nvideos_local" in topic:
        return (topic, topic["nvideos_local"], topic["nvideos_known"], False)

    nvideos_local = 0
    nvideos_known = 0

    # Can't deal with leaves
    assert topic["kind"] == "Topic", "Should not be calling this function on leaves; it's inefficient!"

    # Only look for videos if there are more branches
    if len(topic["children"]) == 0:
        logging.debug("no children: %s" % topic["path"])

    for child in topic["children"]:
        # RECURSIVE CALL:
        #  The children have children, let them figure things out themselves
        if "children" in child:
            if not force and "nvideos_local" in child:
                continue
            stamp_availability_on_topic(topic=child, videos_path=videos_path, force=force, stamp_urls=stamp_urls, update_counts_question_mark=update_counts_question_mark)
            nvideos_local += child["nvideos_local"]
            nvideos_known += child["nvideos_known"]

    # BASE CASE:
    #  Got a topic node, get immediate video children and figure out what to do.
    videos = get_videos(topic)
    for video in videos:
        if force or update_counts_question_mark or "availability" not in video:
            stamp_availability_on_video(video, force=force, stamp_urls=stamp_urls, videos_path=videos_path)
        nvideos_local += int(video["on_disk"])
    nvideos_known += len(videos)
    nvideos_available = nvideos_local if not settings.BACKUP_VIDEO_SOURCE else nvideos_known

    changed = "nvideos_local" in topic and topic["nvideos_local"] != nvideos_local
    changed = changed or ("nvideos_known" in topic and topic["nvideos_known"] != nvideos_known)
    topic["nvideos_local"] = nvideos_local
    topic["nvideos_known"] = nvideos_known
    topic["nvideos_available"] = nvideos_available
    # Topic is available if it contains a downloaded video, or any other resource type (other resources assumed to be downloaded)
    topic["available"] = bool(nvideos_local)
    topic["available"] = topic["available"] or bool(settings.BACKUP_VIDEO_SOURCE)
    topic["available"] = topic["available"] or bool(set(topic.get("contains", [])) - set(["Topic", "Video"]))

    return (topic, nvideos_local, nvideos_known, nvideos_available, changed)
