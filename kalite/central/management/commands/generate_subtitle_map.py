# gen new subtitle mapping

import datetime
import json
import os
import sys
import tempfile

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

import settings
from settings import LOG as logging
from utils.subtitles import subtitle_utils 
from utils.topic_tools import get_node_cache


headers = {
    # "X-api-username": "kalite",
    # "X-apikey": "9931eb077687297823e8a23fd6c2bfafae25c543",
    "X-api-username": "dyl",
    "X-apikey": "6a7e0af81ce95d6b810761041b72412043851804",
}

SRTS_JSON_FILENAME = "srts_api_info.json"
LANGUAGE_SRT_FILENAME = "language_srts_map.json"


class OutDatedSchema(Exception):

    def __str__(value):
        return "The current data schema is outdated and doesn't store the important bits. Please run 'generate_subtitles_map.py -N' to generate a totally new file and the correct schema."


def create_all_mappings(force=False, frequency_to_save=100):
    """Write a new JSON file of mappings from YouTube ID to Amara code"""
    videos = get_node_cache('Video')

    # Initialize the data
    out_file = settings.SUBTITLES_ROOT + SRTS_JSON_FILENAME
    if os.path.exists(out_file):
        with open(out_file, "r") as fp:
            new_json = json.load(fp)
        logging.info("Loaded %d mappings." % (len(new_json)))
    else:
        new_json = {}
    logging.info("Querying %d mappings." % (len(videos) - (0 if force else len(new_json))))

    n_new_entries = 0
    n_failures = 0
    for video, data in videos.iteritems():
        youtube_id = data['youtube_id']
        if youtube_id in new_json and not force:  # allow caching of old results, for easy restart
            continue
        try:
            new_json[youtube_id] = update_video_entry(youtube_id)
        except Exception as e:
            logging.warn("Error updating video %s: %s" % (youtube_id, e))
            n_failures += 1
            continue

        if n_new_entries % frequency_to_save == 0:
            if frequency_to_save > 10:
                logging.info("On loop %d dumping dictionary into %s" %(n_new_entries, out_file))
            with open(out_file, 'wb') as fp:
                json.dump(new_json, fp)
        n_new_entries += 1

    # Finished the loop: save and report
    with open(out_file, 'wb') as fp:
        json.dump(new_json, fp)
    if n_failures == 0:
        logging.info("Great success! Stored %d fresh entries, %d total." % (n_new_entries, len(new_json)))
    else:
        logging.warn("Stored %s fresh entries, but with %s failures." % (n_new_entries, n_failures))


def update_subtitle_map(code_to_check, date_to_check):
    """Update JSON dictionary of subtitle information based on arguments provided"""
    srts_dict = json.loads(open(settings.SUBTITLES_ROOT + SRTS_JSON_FILENAME).read())
    for youtube_id, data in srts_dict.items():
        # ensure response code and date exists
        response_code = data.get("api_response")
        last_attempt = data.get("last_attempt")
        if last_attempt:
            last_attempt = datetime.datetime.strptime(last_attempt, '%Y-%m-%d')

        # HELP: why does the below if statement suck so much? does it suck? it feels like it sucks
        # case: -d AND -s
        flag_for_refresh = not (response_code or last_attempt)
        flag_for_refresh = flag_for_refresh and (not date_to_check or date_to_check > last_attempt)
        flag_for_refresh = flag_for_refresh and (code_to_check == "all" or code_to_check == response_code)

        if flag_for_refresh:
            new_entry = update_video_entry(youtube_id)
            # here we are checking that the original data isn't overwritten by an error response, which only returns last-attempt and api-response
            new_api_response = new_entry["api_response"]
            if new_api_response is not "success":
                srts_dict[youtube_id]["api_response"] = new_api_response
                srts_dict[youtube_id]["last_attempt"] = new_entry["last_attempt"]
            # if it wasn't an error, we simply update the old information with the new
            else: 
                srts_dict[youtube_id].update(new_entry)

    logging.info("Great success! Re-writing JSON file.")
    with open(settings.SUBTITLES_ROOT + SRTS_JSON_FILENAME, 'wb') as fp:
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
        logging.info("%s at %s" %(r, request_url))
        entry["api_response"] = r
    else:
        logging.info("Success at %s" % request_url)
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

def update_language_srt_map(languages=None):
    """Update the language_srt_map from the api_info_map"""

    # Create file if first time being run
    language_srt_filepath = settings.SUBTITLES_ROOT + LANGUAGE_SRT_FILENAME
    if not subtitle_utils.file_already_exists(language_srt_filepath):
        with open(language_srt_filepath, 'w') as outfile:
            json.dump({}, outfile)

    language_srt_map = json.loads(open(language_srt_filepath).read())
    api_info_map = json.loads(open(settings.SUBTITLES_ROOT + SRTS_JSON_FILENAME).read())

    for youtube_id, content in api_info_map.items():
        languages = languages or content.get("language_codes") or []
        for code in languages:
            # create language section if it doesn't exist
            language_srt_map.get(code)
            if not language_srt_map.get(code):
                logging.info("Creating language section '%s'" % code)
                language_srt_map[code] = {}
            # create empty entry for video entry if it doesn't exist
            if not language_srt_map[code].get(youtube_id):
                logging.info("Creating entry in '%s' for YouTube video: '%s'" % (
                    code, youtube_id))
                language_srt_map[code][youtube_id] = {
                    "downloaded": False,
                    "api_response": "",
                    "last_attempt": "",
                    "last_success": "",
                }

    logging.info("Writing updates to %s" % language_srt_filepath)
    with open(language_srt_filepath, 'wb') as fp:
            json.dump(language_srt_map, fp)


class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitledata/video_srts.json"

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help="Force a new mapping. Cannot be run with other options. Fetches new data for every one of our videos and overwrites current data with fresh data from Amara. Should really only ever be run once, because data can be updated from then on with '-s all'.",
                    metavar="FORCE"),
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
        make_option('-l', '--language',
                    action='store',
                    dest='language',
                    default=None,
                    help="Generate for a specific mapping."),
    )

    def handle(self, *args, **options):

        converted_date = subtitle_utils.convert_date_input(options.get("date_since_attempt"))

        create_all_mappings(force=options.get("force"), frequency_to_save=5)
        update_subtitle_map(options.get("response_code"), converted_date)
        logging.info("Executed successfully. Updating language => subtitle mapping to record any changes!")

        update_language_srt_map(languages=[options.get("language")] if options.get("language") else None)
        logging.info("Process complete.")
        sys.exit(1)
