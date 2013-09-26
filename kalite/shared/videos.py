import settings
import utils.videos  # keep access to all functions
from shared.topic_tools import get_topic_tree, get_videos
from utils.videos import *  # get all into the current namespace, override some.


def get_video_ids_for_topic(topic_id, topic_tree=None):
    """Nobody actually calls this, just for utility when using the shell."""
    topic_tree = topic_tree or get_topic_tree()
    return utils.videos.get_video_ids_for_topic(topic_id, topic_tree)


def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_url = ("http://%s/download/videos/" % (settings.CENTRAL_SERVER_HOST)) + "%s/%s"
    return utils.videos.download_video(youtube_id, settings.CONTENT_ROOT, download_url, format, callback)


def delete_downloaded_files(youtube_id):
    return utils.videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)


def get_video_urls(video_id, format, video_on_disk=True):
    disk_path = settings.CONTENT_URL + video_id

    if not video_on_disk and settings.BACKUP_VIDEO_SOURCE:
        dict_vals = {"video_id": video_id, "video_format": format, "thumb_format": "png" }
        stream_url = settings.BACKUP_VIDEO_SOURCE % dict_vals
        thumbnail_url = settings.BACKUP_THUMBNAIL_SOURCE % dict_vals if settings.BACKUP_THUMBNAIL_SOURCE else None
        subtitles_url = disk_path + ".srt"
    else:
        stream_url = disk_path + ".%s" % format
        thumbnail_url = disk_path + ".png"
        subtitles_url = disk_path + ".srt"

    return (stream_url, thumbnail_url, subtitles_url)


def is_video_on_disk(youtube_id, videos_path=settings.CONTENT_ROOT, format="mp4"):
    return os.path.isfile(videos_path + youtube_id + ".%s" % format)


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


def get_video_counts(topic, videos_path, force=False):
    """ Uses the (json) topic tree to query the django database for which video files exist

    Returns the original topic dictionary, with two properties added to each NON-LEAF node:
      * nvideos_known: The # of videos in and under that node, that are known (i.e. in the Khan Academy library)
      * nvideos_local: The # of vidoes in and under that node, that were actually downloaded and available locally
    And the following property for leaf nodes:
      * on_disk

    Input Parameters:
    * videos_path: the path to video files
    """

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
                (child, _, _) = get_video_counts(topic=child, videos_path=videos_path)
                nvideos_local += child["nvideos_local"]
                nvideos_known += child["nvideos_known"]

        # BASE CASE:
        # All my children are leaves, so we'll query here (a bit more efficient than 1 query per leaf)
        else:
            videos = get_videos(topic)
            if len(videos) > 0:

                for video in videos:
                    # Mark all videos as not found
                    video["on_disk"] = is_video_on_disk(video["youtube_id"], videos_path)
                    nvideos_local += int(video["on_disk"])  # add 1 if video["on_disk"]
                nvideos_known = len(videos)

    topic["nvideos_local"] = nvideos_local
    topic["nvideos_known"] = nvideos_known
    return (topic, nvideos_local, nvideos_known)