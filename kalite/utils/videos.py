import sys, os, re, json, urllib, glob

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path = [PROJECT_PATH] + sys.path

import settings

download_path = settings.CONTENT_ROOT

data_path = settings.DATA_PATH

download_url = "http://s3.amazonaws.com/KA-youtube-converted/%s/%s"


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
    topic_tree = topic_tree or json.loads(open(data_path + "topics.json").read())
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

def download_all_videos(topic="root"):
    all_youtube_ids = get_video_ids_for_topic(topic)
    for id in all_youtube_ids:
        download_video(id)
        # print id

# http://code.activestate.com/recipes/82465-a-friendly-mkdir/
def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)

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

def download_video(youtube_id, format="mp4", callback=None):
    
    _mkdir(download_path)
    
    video_filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    filepath = download_path + video_filename
    url = download_url % (video_filename, video_filename)
    
    large_thumb_filename = "%(id)s.png" % {"id": youtube_id}
    large_thumb_filepath = download_path + large_thumb_filename
    large_thumb_url = download_url % (video_filename, large_thumb_filename)
    
    thumb_filepath = download_path + youtube_id + ".jpg"
    thumb_url = "http://img.youtube.com/vi/%(id)s/hqdefault.jpg" % {"id": youtube_id}
    
    try:
        download_file(url, filepath, callback_percent_proxy(callback, end_percent=91))
        
        download_file(large_thumb_url, large_thumb_filepath, callback_percent_proxy(callback, start_percent=91, end_percent=96))

        download_file(thumb_url, thumb_filepath, callback_percent_proxy(callback, start_percent=96, end_percent=100))
        
    except DownloadCancelled:
        delete_downloaded_files(youtube_id)
        
def delete_downloaded_files(youtube_id):
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
    urllib.urlretrieve(url, dst,
        lambda nb, bs, fs, url=url: callback(nb,bs,fs,url))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("topic:"):
            download_all_videos(sys.argv[1].split(":")[1])
        else:
            download_video(sys.argv[1])
    else:
        print "USAGE: python videos.py (<youtube_id> | topic:<topic_id>)"
    