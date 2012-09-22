import requests, sys, os, re

download_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/videos/"

data_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/data/"

download_url = "http://s3.amazonaws.com/KA-youtube-converted/%s/%s"

def download_all_videos():
    all_youtube_ids = list(set(re.findall("youtube_id\": \"([^\"]+)\"", open(data_path + "topics.json").read())))
    for id in all_youtube_ids:
        download_video(id)

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

def download_video(youtube_id, format="mp4"):
    
    _mkdir(download_path)
    
    filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    filepath = download_path + filename
    url = download_url % (filename, filename)
    download_file(url, filepath)
    
    large_thumb_filename = "%(id)s.png" % {"id": youtube_id}
    large_thumb_filepath = download_path + large_thumb_filename
    large_thumb_url = download_url % (filename, large_thumb_filename)
    download_file(large_thumb_url, large_thumb_filepath)
    
    thumb_filepath = download_path + youtube_id + ".jpg"
    thumb_url = "http://img.youtube.com/vi/%(id)s/hqdefault.jpg" % {"id": youtube_id}
    download_file(thumb_url, thumb_filepath)
    
    exercise_filepath = download_path + youtube_id + "_exercises.json"
    exercise_url = "http://www.khanacademy.org/api/v1/videos/%(id)s/exercises" % {"id": youtube_id}
    download_file(exercise_url, exercise_filepath)
    

def download_file(url, filepath):
    download = requests.get(url)
    filesize = int(download.headers['content-length'] or 1)

    CHUNK = 128 * 1024
    with open(filepath, 'wb') as fp:
        i = 0
        print "     (%s)" % url,
        while True:
            print "\r%d%%" % min(round((i * CHUNK * 100.0) / filesize), 100),
            sys.stdout.flush()
            chunk = download.raw.read(CHUNK)
            if not chunk:
                break
            fp.write(chunk)
            i += 1
        print ""

if __name__ == '__main__':
    if len(sys.argv) > 1:
        download_video(sys.argv[1])
    else:
        print "USAGE: python videos.py <youtube_id>"
    