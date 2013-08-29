import settings
import utils.videos  # keep access to all functions
from utils.videos import *  # get all into the current namespace, override some.
from utils.topic_tools import get_topic_tree


def get_video_ids_for_topic(topic_id, topic_tree=None):
    """Nobody actually calls this, just for utility when using the shell."""
    topic_tree = topic_tree or get_topic_tree()
    return utils.videos.get_video_ids_for_topic(topic_id, topic_tree)

def download_all_videos(topic="root"):
    """Nobody actually calls this, just for utility when using the shell."""
    all_youtube_ids = get_video_ids_for_topic(topic)
    for id in all_youtube_ids:
        download_video(id)
        # print id

def download_video(youtube_id, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""

    download_path = settings.CONTENT_ROOT
    return utils.videos.download_video(youtube_id, settings.CONTENT_ROOT, format, callback)

def delete_downloaded_files(youtube_id):
    return utils.videos.delete_downloaded_files(youtube_id, settings.CONTENT_ROOT)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("topic:"):
            download_all_videos(sys.argv[1].split(":")[1])
        else:
            download_video(sys.argv[1])
    else:
        print "USAGE: python videos.py (<youtube_id> | topic:<topic_id>)"
