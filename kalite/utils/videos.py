import requests, sys, os

download_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/videos/"

download_url = "http://s3.amazonaws.com/KA-youtube-converted/%s/%s"

def download_video(youtube_id, format="mp4"):
    
    filename = "%(id)s.%(format)s" % {"id": youtube_id, "format": format}
    filepath = download_path + filename
    url = download_url % (filename, filename)
    download_file(url, filepath)
    
    thumb_filename = "%(id)s.png" % {"id": youtube_id}
    thumb_filepath = download_path + thumb_filename
    thumb_url = download_url % (filename, thumb_filename)
    download_file(thumb_url, thumb_filepath)


def download_file(url, filepath):
    download = requests.get(url)
    filesize = int(download.headers['content-length'])

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
    