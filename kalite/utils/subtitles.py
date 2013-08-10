import requests, sys, urllib2

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path = [PROJECT_PATH] + sys.path

import settings

def download_subtitles(language):
    """Return zip of subtitles for specified language"""
    
    central_url = settings.CENTRAL_SERVER_DOMAIN
    file_name = "%s_subtitles.zip" % language

    response = urllib2.urlopen(central_url)
    f = open(file_name, 'wb')
    meta = response.info()
    file_size = int(meta.getheaders("Content-Length")[0])

    file_size_dl = 0
    block_size = 8192
    while True:
        buffer = response.read(block_size)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

    zipped_subs = requests.get("%s/download/subtitles/%s" % (central_url, language))

    return zipped_subs
