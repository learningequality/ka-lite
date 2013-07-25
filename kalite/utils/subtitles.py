import requests, json, os, sys

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../"

sys.path = [PROJECT_PATH] + sys.path

import settings
import version

download_path = settings.CONTENT_ROOT

headers = {
    "X-api-username": "kalite",
    "X-apikey": "9931eb077687297823e8a23fd6c2bfafae25c543",
}

base_url = "http://%s/static/data/subtitles" % settings.CENTRAL_SERVER_HOST

class NoSubs(Exception):
    
    def __str__(value):
        return "No Subtitles for this video"

def get_subtitles(youtube_id, language):
    import pdb; pdb.set_trace()

    # use the Amara video id to get the subtitles and translated metadata in the target language
    r = requests.get("%s/%s/%s.srt" % (base_url, language, youtube_id), headers={ "User-Agent": "KA-Lite %s" % version.VERSION})
    # return the subtitle text, replacing empty subtitle lines with spaces to make the FLV player happy
    return (r.text or "").replace("\n\n\n", "\n   \n\n").replace("\r\n\r\n\r\n", "\r\n   \r\n\r\n")

def download_subtitles(youtube_id, language):
    
    subtitles = get_subtitles(youtube_id, language)
    
    if subtitles:
    
        filepath = download_path + "%s.srt" % youtube_id
        
        with open(filepath, 'w') as fp:
            fp.write(subtitles.encode('UTF-8'))
    
    else:
        raise NoSubs()


if __name__ == '__main__':
    language = "en"
    if len(sys.argv) > 2:
        language = sys.argv[2]
    if len(sys.argv) > 1:
        youtube_id = sys.argv[1]
        download_subtitles(youtube_id, language)
        print "Downloaded subtitles for video '%s' in language '%s'!" % (youtube_id, language)
    else:
        print "USAGE: python subtitles.py <youtube_id> [<language>]"
    
