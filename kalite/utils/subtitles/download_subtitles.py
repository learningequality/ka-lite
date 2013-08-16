import json
import os
import requests
import sys

import settings

download_path = settings.CONTENT_ROOT

class NoSubs(Exception):
    
    def __str__(value):
        return "No Subtitles for this video"

def get_subtitles(youtube_id, language, format="srt"):
    
    r = requests.get("http://%s/static/srt/%s/subtitles/%s.srt" % (settings.CENTRAL_SERVER_HOST, language, youtube_id))
    if r.status_code > 399:
        raise NoSubs()

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
    