import argparse
import json
import sys
import os
import pdb

import requests

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path = [PROJECT_PATH, os.path.join(PROJECT_PATH, "../"), os.path.join(
    PROJECT_PATH, "../python-packages/")] + sys.path

import settings

download_path = settings.LOCALE_PATHS[0]

base_url = "https://amara.org/api2/partners/videos"

srts_dict = json.loads(open(os.path.dirname(
    os.path.realpath(__file__)) + "/../static/data/video_srts.json").read())

headers = {
    # "X-api-username": "kalite",
    # "X-apikey": "9931eb077687297823e8a23fd6c2bfafae25c543",
    "X-api-username": "dyl",
    "X-apikey": "6a7e0af81ce95d6b810761041b72412043851804",
}


class NoSubs(Exception):

    def __str__(value):
        return "No Subtitles for this video"


def get_subtitles(youtube_id, language, format="json"):
    """Return subtitles for YouTube ID in language specified. Return False if they do not exist."""

    # If not yet in local JSON file, go and get it, then reference the local file to get Amara ID
    if youtube_id not in srts_dict:
        update_srts_dict(get_amara_info(youtube_id))
    amara_video_id = srts_dict.get(youtube_id).get("amara_code")

    # use the Amara video id to get the subtitles and translated metadata in
    # the target language
    if format == "json":
        r = make_request("%s/%s/languages/%s/subtitles/" % (
            base_url, amara_video_id, language))
        if r:
            subtitles = json.loads(r.text)
            return subtitles
    elif format == "srt":
        r = make_request("%s/%s/languages/%s/subtitles/?format=srt" % (
            base_url, amara_video_id, language))
        if r:
            # return the subtitle text, replacing empty subtitle lines with
            # spaces to make the FLV player happy
            return (r.text or "").replace("\n\n\n", "\n   \n\n").replace("\r\n\r\n\r\n", "\r\n   \r\n\r\n")
    return False


def update_srts_dict(video_info_dict):
    """Dump passed dictionary into local JSON file"""

    json_file = open("video_srts.json", "r")
    srts_dict = json.load(json_file)
    json_file.close()

    srts_dict.update(video_info_dict)

    json_file = open("video_srts.json", "w+")
    json_file.write(json.dumps(srts_dict))
    json_file.close()


def get_amara_info(youtube_id, format="json"):
    """Return a dictionary in the below format to update the local JSON file with.

        { youtube_id: {
                "amara_code": "3x4mp1e"
                "language_codes": ["en", "es", "etc"]
            }
        }

    """
    video_srt_dict[youtube_id] = {
        "amara_code": "",
        "language_codes": []
    }

    r = make_request("%s?format=json&video_url=http://www.youtube.com/watch?v=%s" %
                     (base_url, youtube_id))
    if r:
        content = json.loads(r.text)
        if content.get("objects"):
            languages = json.loads(r.content)['objects'][0]['languages']
            if len(languages) > 0:
                amara_code = languages[0].get("subtitles_uri").split("/")[4]
                assert len(amara_code) == 12
                video_srt_dict.get(youtube_id)["amara_code"] = amara_code
                for language in languages:
                    video_srt_dict.get(youtube_id)[
                        "language_codes"].append(language['code'])
                        
    # will return empty if we don't get a valid response from make_request
    return video_srt_dict


def make_request(url):
    """Return response from url; retry up to 5 times, otherwise, skip"""
    if not known_bad_url(url):
        for retries in range(1, 5):
            try:
                r = requests.get(url, headers=headers)
            except requests.exceptions.Timeout:
                # retry if there are still retries left
                print "Error: Timeout"
                if retries < 5:
                    print "continuing... retries left: %s" % str(retries)
                else:
                    break
            except requests.exceptions.TooManyRedirects:
                print "Error: Too many redirects"
                break
            except requests.exceptions.RequestException as e:
                # catastrophic error. bail.
                print e
                sys.exit(1)
            else:
                if r.status_code > 499:
                    print "Server error: %s at %s" % (str(r.status_code), url)
                    if retries == 4:
                        print "Maxed out retries: adding %s to bad urls list" % url
                        add_to_bad_url_list(url)
                elif r.status_code > 399:
                    print "Client error: %s at %s" % (str(r.status_code), url)
                    print "Adding %s to bad urls list" % url
                    add_to_bad_url_list(url)
                    break
                else:
                    print "Good request: %s at %s" % (str(r.status_code), url)
                    return r
    return False

def file_already_exists(youtube_id, language):
    file_exists = False
    fullpath = download_path + language + "/subtitles/" + youtube_id + ".srt" 
    if os.path.exists(fullpath):
        file_exists = True
    return file_exists

def known_bad_url(url):
    is_broken = False
    bad_urls = json.loads(open(os.path.dirname(os.path.realpath(__file__)) + "/../static/data/bad_amara_urls.json").read())
    if url in bad_urls["bad_urls"]:
        is_broken = True
    return is_broken


def add_to_bad_url_list(url):
    json_file = open(os.path.dirname(os.path.realpath(__file__)) + "/../static/data/bad_amara_urls.json")
    bad_urls = json.load(json_file)
    json_file.close()

    bad_urls["bad_urls"].append(url)

    json_file = open(os.path.dirname(os.path.realpath(__file__)) + "/../static/data/bad_amara_urls.json", "w+")
    json_file.write(json.dumps(bad_urls))
    json_file.close()


def download_subtitles(youtube_id, language):

    if file_already_exists(youtube_id, language):
        print "Already downloaded"
        return False
    else: 
        subtitles = get_subtitles(youtube_id, language, format="srt")

        if subtitles:

            # placing them directly into locale folder
            filepath = download_path + language + "/subtitles/"
            filename = youtube_id + ".srt" 
            fullpath = filepath + filename
            print "Writing file to %s" % (fullpath)

            if not os.path.exists(filepath):
                os.makedirs(filepath)

            with open(fullpath, 'w') as fp:
                fp.write(subtitles.encode('UTF-8'))
            return True

        else:
            print "No subs"
            # raise NoSubs()
            return False

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
