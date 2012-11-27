import requests, json, os, sys

download_path = os.path.dirname(os.path.realpath(__file__)) + "/../static/videos/"

headers = {
    "X-api-username": "",
    "X-apikey": "",
}

base_url = "https://www.universalsubtitles.org/api2/partners/videos"

class NoSubs(Exception):
    
    def __str__(value):
        return "No Subtitles for this video"

def get_subtitles(youtube_id, language, format="json"):
    
    # use the base video endpoint to get the Amara video id from the Youtube ID
    r = requests.get("%s?video_url=http://www.youtube.com/watch?v=%s" % (base_url, youtube_id), headers=headers)
    content = json.loads(r.text)
    if content.has_key("objects"):
        video_id = json.loads(r.text)["objects"][0]["id"]
    else:
        return False
    
    # use the Amara video id to get the subtitles and translated metadata in the target language
    if format=="json":
        r = requests.get("%s/%s/languages/%s/subtitles/" % (base_url, video_id, language), headers=headers)
        subtitles = json.loads(r.text)
        return subtitles
    elif format=="srt":
        r = requests.get("%s/%s/languages/%s/subtitles/?format=srt" % (base_url, video_id, language), headers=headers)
        # return the subtitle text, replacing empty subtitle lines with spaces to make the FLV player happy
        return (r.text or "").replace("\n\n\n", "\n   \n\n").replace("\r\n\r\n\r\n", "\r\n   \r\n\r\n")

def download_subtitles(youtube_id, language):
    
    subtitles = get_subtitles(youtube_id, language, format="srt")
    
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
    
