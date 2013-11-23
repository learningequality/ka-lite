import os

import settings
import utils.videos  # keep access to all functions
from settings import logging
from shared.i18n import get_srt_path_on_disk, get_srt_url, get_id2oklang_map, get_youtube_id, get_installed_subtitles
from shared.topic_tools import get_topic_tree, get_videos
from utils.videos import *  # get all into the current namespace, override some.


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"
    return utils.videos.download_video(youtube_id, settings.CONTENT_ROOT, download_url, format, callback)


def delete_downloaded_files(youtube_id):
    return utils.videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)


def get_video_urls(video_id, format="mp4", language_codes=[], videos_path=settings.CONTENT_ROOT):
    """
    Returns a dictionary specifying:
    * All of the available subtitles
    * For each file available on disk, the stream URL, and thumbnail URL
    * For each video available through the web, the stream URL and thumbnail URL
    """

    def compute_urls(youtube_id, format, thumb_format="png", videos_path=settings.CONTENT_ROOT):
        video_on_disk = is_video_on_disk(youtube_id, format, videos_path=videos_path)

        if not video_on_disk and settings.BACKUP_VIDEO_SOURCE:
            dict_vals = {"youtube_id": youtube_id, "video_format": format, "thumb_format": thumb_format }
            stream_url = settings.BACKUP_VIDEO_SOURCE % dict_vals
            thumbnail_url = settings.BACKUP_THUMBNAIL_SOURCE % dict_vals if settings.BACKUP_THUMBNAIL_SOURCE else None
        else:
            video_base_url = settings.CONTENT_URL + youtube_id
            stream_url = video_base_url + ".%s" % format
            thumbnail_url = video_base_url + ".png"
        return {"stream_url": stream_url, "thumbnail_url": thumbnail_url, "on_disk": video_on_disk, "stream_type": "video/%s" % format}

    youtube_id = get_youtube_id(video_id, None)

    urls = {}

    # Get the subtitle urls
    subtitles_tuple = [(code, get_srt_url(youtube_id, code)) for code in language_codes if os.path.exists(get_srt_path_on_disk(youtube_id, code))]
    subtitles_urls = dict(subtitles_tuple)

    # Loop over all known dubbed videos
    for language, youtube_id in get_id2oklang_map(video_id).iteritems():
        urls[language] = compute_urls(youtube_id, format, thumb_format="png", videos_path=videos_path)
        urls[language]["subtitles"] = subtitles_urls

    # now scrub any values that don't actually exist
    for lang in urls.keys():
        if not urls[lang]["on_disk"]:
            del urls[lang]
    print urls
    return urls

def stamp_urls_on_video(video, force=False):
    """
    Stamp all relevant urls onto a video object (if necessary), including:
    * whether the video is available (on disk or online)
    """
    if force or "urls" not in video:
        logging.debug("Adding urls into video %s" % video["path"])

    # Compute video URLs.  Must use videos from topics, as the NODE_CACHE doesn't contain all video objects. :-/
    language_codes = get_installed_subtitles(video["youtube_id"])
    video["urls"] = get_video_urls(
        video_id=video["id"],
        format="mp4",
        language_codes=language_codes,
    )
    video["available"] = bool(video["urls"]) or bool(settings.BACKUP_VIDEO_SOURCE)
    return video

def is_video_on_disk(youtube_id, format="mp4", videos_path=settings.CONTENT_ROOT):
    return os.path.isfile(os.path.join(videos_path, youtube_id + ".%s" % format))


_vid_last_updated = 0
_vid_last_count = 0
def video_counts_need_update(videos_path=settings.CONTENT_ROOT):
    """
    Compare current state to global state variables to check whether video counts need updating.
    """
    global _vid_last_count
    global _vid_last_updated

    if not os.path.exists(videos_path):
        return False

    files = os.listdir(videos_path)

    vid_count = len(files)
    if vid_count:
        # TODO(bcipolli) implement this as a linear search, rather than sort-then-select.
        vid_last_updated = os.path.getmtime(sorted([(videos_path + f) for f in files], key=os.path.getmtime, reverse=True)[0])
    else:
        vid_last_updated = 0
    need_update = (vid_count != _vid_last_count) or (vid_last_updated != _vid_last_updated)

    _vid_last_count = vid_count
    _vid_last_updated = vid_last_updated

    return need_update


def get_video_counts(topic, videos_path=settings.CONTENT_ROOT, force=False):
    """ Uses the (json) topic tree to query the django database for which video files exist

    Returns the original topic dictionary, with two properties added to each NON-LEAF node:
      * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan Academy library)
      * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
    And the following property for leaf nodes:
      * on_disk

    Input Parameters:
    * videos_path: the path to video files
    """

    if not force and "nvideos_local" in topic:
        return (topic, topic["nvideos_local"], topic["nvideos_known"], False)

    nvideos_local = 0
    nvideos_known = 0

    # Can't deal with leaves
    assert "children" in topic, "Should not be calling this function on leaves; it's inefficient!"

    # Only look for videos if there are more branches
    if len(topic["children"]) == 0:
        logging.debug("no children: %s" % topic["path"])

    elif len(topic["children"]) > 0:
        # RECURSIVE CALL:
        #  The children have children, let them figure things out themselves
        # $ASSUMPTION: if first child is a branch, THEY'RE ALL BRANCHES.
        #              if first child is a leaf, THEY'RE ALL LEAVES
        if "children" in topic["children"][0]:
            for child in topic["children"]:
                if not force and "nvideos_local" in child:
                    continue
                (child, _, _, _) = get_video_counts(topic=child, videos_path=videos_path)
                nvideos_local += child["nvideos_local"]
                nvideos_known += child["nvideos_known"]

        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = get_videos(topic)
            for video in videos:
                if force or "urls" not in video:
                    stamp_urls_on_video(video)
                nvideos_local += int(bool(video["urls"]))  # add 1 if video["on_disk"]
            nvideos_known = len(videos)

    changed = topic.get("nvideos_local", -1) != nvideos_local
    changed = changed or topic.get("nvideos_known", -1) != nvideos_known
    topic["nvideos_local"] = nvideos_local
    topic["nvideos_known"] = nvideos_known
    return (topic, nvideos_local, nvideos_known, changed)
