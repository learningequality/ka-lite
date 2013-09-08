import glob
import json
import os
import re
import socket
import sys
import urllib

import utils.internet
from utils.general import ensure_dir

socket.setdefaulttimeout(20)

OUTSIDE_DOWNLOAD_BASE_URL = "http://s3.amazonaws.com/KA-youtube-converted/"  # needed for redirects
OUTSIDE_DOWNLOAD_URL = OUTSIDE_DOWNLOAD_BASE_URL + "%s/%s"  # needed for default behavior, below


class DownloadCancelled(Exception):
    def __str__(self):
        return "Download has been cancelled"


def get_video_ids(topic_tree):
    if topic_tree["kind"] == "Video":
        return [topic_tree["youtube_id"]]
    elif topic_tree["kind"] == "Topic":
        results = []
        for kid in topic_tree.get("children", []):
            results += get_video_ids(kid)
        return results
    else:
        return []

def get_video_ids_for_topic(topic_id, topic_tree=None):
    if topic_tree["kind"] != "Topic":
        return []
    if topic_tree.get("id", "") == topic_id:
        return list(set(get_video_ids(topic_tree)))
    else:
        for kid in topic_tree.get("children", []):
            ids = get_video_ids_for_topic(topic_id, kid)
            if ids:
                return ids
        return []

def download_all_videos(topic="root", download_path="../content/", download_url=OUTSIDE_DOWNLOAD_URL, format="mp4", callback=None):
    all_youtube_ids = get_video_ids_for_topic(topic)
    for id in all_youtube_ids:
        download_video(id, download_path, downlod_url=download_url, format=format, callback=callback)
        # print id

def callback_percent_proxy(callback, start_percent=0, end_percent=100):
    if not callback:
        return None
    percent_range_size = end_percent - start_percent
    def inner_fn(numblocks, blocksize, filesize, *args, **kwargs):
        if filesize <= 0:
            filesize = blocksize
        try:
            fraction = min(float(numblocks*blocksize)/filesize, 1.0)
        except:
            fraction = 1.0
        callback(start_percent + int(fraction * percent_range_size))
    return inner_fn

class URLNotFound(Exception):
    pass

def download_video(youtube_id, download_path="../content/", download_url=OUTSIDE_DOWNLOAD_URL, format="mp4", callback=None):
    """Downloads the video file to disk (note: this does NOT invalidate any of the cached html files in KA Lite)"""
    
    ensure_dir(download_path)
    
    video_filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    filepath = download_path + video_filename
    url = download_url % (video_filename, video_filename)
    
    thumb_filename = "%(id)s.png" % {"id": youtube_id}
    thumb_filepath = download_path + thumb_filename
    thumb_url = download_url % (video_filename, thumb_filename)
        
    try:
        path, response = download_file(url, filepath, callback_percent_proxy(callback, end_percent=95))
        if not response.type.startswith("video"):
            raise URLNotFound("Video was not found!")
        
        path, response = download_file(thumb_url, thumb_filepath, callback_percent_proxy(callback, start_percent=95, end_percent=100))
        if not response.type.startswith("image"):
            raise URLNotFound("Thumbnail was not found!")
        
    except DownloadCancelled:
        delete_downloaded_files(youtube_id, download_path)
    
    except Exception as e:
        delete_downloaded_files(youtube_id, download_path)
        raise
    
def delete_downloaded_files(youtube_id, download_path):
    for filepath in glob.glob(download_path + youtube_id + ".*"):
        try:
            os.remove(filepath)
        except OSError:
            pass

def _reporthook(numblocks, blocksize, filesize, url=None):
    base = os.path.basename(url)
    if filesize <= 0:
        filesize = blocksize
    try:
        percent = min((numblocks*blocksize*100)/filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b"*40)
    sys.stdout.write("%-36s%3d%%" % (base, percent))
    if percent == 100:
        sys.stdout.write("\n")

def _nullhook(*args, **kwargs):
    pass

def download_file(url, dst, callback=None):
    if sys.stdout.isatty():
        callback = callback or _reporthook
    else:
        callback = callback or _nullhook
    return urllib.urlretrieve(url, dst, lambda nb, bs, fs, url=url: callback(nb,bs,fs,url))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("topic:"):
            download_all_videos(sys.argv[1].split(":")[1])
        else:
            download_video(sys.argv[1])
    else:
        print "USAGE: python videos.py (<youtube_id> | topic:<topic_id>)"
    