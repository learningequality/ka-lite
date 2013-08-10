# gen new subtitle mapping

import datetime
import json
import logging
import os
import sys
import tempfile

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../../"
sys.path = [PROJECT_PATH] + sys.path
import settings
from utils.subtitles import subtitle_utils 

headers = {
    "X-api-username": "kalite",
    "X-apikey": "9931eb077687297823e8a23fd6c2bfafae25c543",
}

data_path = settings.DATA_PATH + "subtitledata/"

logger = subtitle_utils.setup_logging("generate_subtitle_map")

SRTS_JSON_FILENAME = "srts_api_info.json"

LANGUAGE_SRT_FILENAME = "language_srts_map.json"

class OutDatedSchema(Exception):

    def __str__(value):
        return "The current data schema is outdated and doesn't store the important bits. Please run 'generate_subtitles_map.py -N' to generate a totally new file and the correct schema."


def create_new_mapping():
    """Write a new JSON file of mappings from YouTube ID to Amara code"""
    nodecache = json.load(open(data_path + '../nodecache.json', 'r'))
    videos = nodecache['Video']
    new_json = {}
    counter = 0
    for video, data in videos.iteritems():
        youtube_id = data['youtube_id']
        new_json[youtube_id] = update_video_entry(youtube_id)
        # TODO(dylan) 3000+ videos - can't expect process to complete before
        # saving. HELP: is this the best interim step?
        if counter%200 == 0:
            temp_file = "temp_video_srts.json"
            logger.info("On loop %s dumping dictionary into temp file static/data/subtitledata/: %s" %(str(counter), temp_file))
            with open(data_path + temp_file, 'wb') as fp:
                json.dump(new_json, fp)
        counter += 1
    logger.info("Great success! Stored %s fresh entries." % str(counter))
    with open(data_path + SRTS_JSON_FILENAME, 'wb') as fp:
        json.dump(new_json, fp)
    logger.info("Deleting temp file....")
    os.remove(data_path + temp_file)


def update_subtitle_map(code_to_check, date_to_check):
    """Update JSON dictionary of subtitle information based on arguments provided"""
    srts_dict = json.loads(open(data_path + SRTS_JSON_FILENAME).read())
    for youtube_id, data in srts_dict.items():
        # ensure response code and date exists
        response_code = data.get("api_response")
        last_attempt = data.get("last_attempt")
        if last_attempt:
            last_attempt = datetime.datetime.strptime(last_attempt, '%Y-%m-%d')
        if not (response_code or last_attempt):
            raise OutDatedSchema()

        # HELP: why does the below if statement suck so much? does it suck? it feels like it sucks
        # case: -d AND -s
        flag_filter = False
        if date_to_check and code_to_check:
            if date_to_check < last_attempt and code_to_check == "all" or code_to_check == response_code:
                flag_filter = True
        # case: -d only
        elif date_to_check and not code_to_check:
            if date_to_check < last_attempt:
                flag_filter = True
        # case: -s only
        elif code_to_check and not date_to_check:
            if code_to_check == "all" or code_to_check == response_code:
                flag_filter = True

        if flag_filter:
            new_entry = update_video_entry(youtube_id)
            # here we are checking that the original data isn't overwritten by an error response, which only returns last-attempt and api-response
            new_api_response = new_entry["api_response"]
            if new_api_response is not "success":
                srts_dict[youtube_id]["api_response"] = new_api_response
                srts_dict[youtube_id]["last_attempt"] = new_entry["last_attempt"]
            # if it wasn't an error, we simply update the old information with the new
            else: 
                srts_dict[youtube_id].update(new_entry)

    logger.info("Great success! Re-writing JSON file.")
    with open(data_path + SRTS_JSON_FILENAME, 'wb') as fp:
        json.dump(srts_dict, fp)

def update_video_entry(youtube_id):
    """Return a dictionary to be appended to the current schema:
            youtube_id: {
                            "amara_code": "3x4mp1e",
                            "language_codes": ["en", "es", "etc"],
                            "api_response": "success" OR "client_error" OR "server_error",
                            "last_success": "2013-07-06",
                            "last_attempt": "2013-07-06",
                        }

    """
    request_url = "https://www.amara.org/api2/partners/videos/?format=json&video_url=http://www.youtube.com/watch?v=%s" % (
        youtube_id)
    r = subtitle_utils.make_request(headers, request_url)
    # add api response first to prevent empty json on errors
    entry = {}
    entry["last_attempt"] = unicode(datetime.datetime.now().date())
    if r == "client_error" or r == "server_error":
        logger.info("%s at %s" %(r, request_url))
        entry["api_response"] = r
    else:
        logger.info("Success at %s" % request_url)
        entry["api_response"] = "success"
        entry["last_success"] = unicode(datetime.datetime.now().date())
        content = json.loads(r.content)
        # index into data to extract languages and amara code, then add them
        if content.get("objects"):
            languages = json.loads(r.content)['objects'][0]['languages']
            entry["language_codes"] = []
            if languages:  # ensuring it isn't an empty list
                # add the codes and then
                for language in languages:
                    entry["language_codes"].append(language['code'])
                # pull amara video id
                amara_code = languages[0].get("subtitles_uri").split("/")[4]
                assert len(amara_code) == 12  # in case of future API change
                entry["amara_code"] = amara_code
    return entry

def update_language_srt_map():
    """Update the language_srt_map from the api_info_map"""

    # Create file if first time being run
    language_srt_filepath = data_path + LANGUAGE_SRT_FILENAME
    if not subtitle_utils.file_already_exists(language_srt_filepath):
        with open(language_srt_filepath, 'w') as outfile:
            json.dump({}, outfile)

    language_srt_map = json.loads(open(language_srt_filepath).read())
    api_info_map = json.loads(open(data_path + SRTS_JSON_FILENAME).read())

    for youtube_id, content in api_info_map.items():
        lang_list = content.get("language_codes") or []
        for code in lang_list:
            # create language section if it doesn't exist
            language_srt_map.get(code)
            if not language_srt_map.get(code):
                logger.info("Creating language section '%s'" % code)
                language_srt_map[code] = {}
            # create empty entry for video entry if it doesn't exist
            if not language_srt_map[code].get(youtube_id):
                logger.info("Creating entry in '%s' for YouTube video: '%s'" % (
                    code, youtube_id))
                language_srt_map[code][youtube_id] = {
                    "downloaded": False,
                    "api_response": "",
                    "last_attempt": "",
                    "last_success": "",
                }

    logger.info("Writing updates to %s" % language_srt_filepath)
    with open(language_srt_filepath, 'wb') as fp:
            json.dump(language_srt_map, fp)


class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitledata/video_srts.json"

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-N', '--new',
                    action='store_true',
                    dest='new',
                    default=False,
                    help="Force a new mapping. Cannot be run with other options. Fetches new data for every one of our videos and overwrites current data with fresh data from Amara. Should really only ever be run once, because data can be updated from then on with '-s all'.",
                    metavar="NEW"),
        make_option('-r', '--response_code',
                    action='store',
                    dest='response_code',
                    default=None,
                    help="Which api-response code to recheck. Can be combined with -d. USAGE: '-r all', '-r client-error', or '-r server-error'.",
                    metavar="RESPONSE_CODE"),
        make_option('-d', '--date_since_attempt',
                    action='store',
                    dest='date_since_attempt',
                    default=None,
                    help="Setting a date flag will update only those entries which have not been attempted since that date. Can be combined with -r. This could potentially be useful for updating old subtitles. USAGE: '-d MM/DD/YYYY'"),
    )

    def handle(self, *args, **options):
        if options.get("new") and not (options.get("response_code") or options.get("date_since_attempt")):
            create_new_mapping()
        elif not options.get("new") and (options.get("response_code") or options.get("date_since_attempt")):
            converted_date = subtitle_utils.convert_date_input(
                options.get("date_since_attempt"))
            update_subtitle_map(options.get("response_code"), converted_date)
        else:
            raise CommandError(
                "Invalid input. Please read the usage instructions more carefully and try again.")
            
        logger.info("Executed successfully. Updating language => subtitle mapping to record any changes!")
        update_language_srt_map()

        logger.info("Process complete.")
        sys.exit(1)
