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

SRTS_JSON_FILENAME = "srts_remote_availability.json"
LANGUAGE_SRT_FILENAME = "srts_download_status.json"


class OutDatedSchema(Exception):
    def __str__(self):
        return "The current data schema is outdated and doesn't store the important bits. Please run 'generate_subtitles_map.py -N' to generate a totally new file and the correct schema."


def create_all_mappings(force=False, frequency_to_save=100, date_to_check=None):
    """Write a new JSON file of mappings from YouTube ID to Amara code"""
    videos = get_node_cache('Video')

    # Initialize the data
    out_file = settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME

    if not os.path.exists(out_file):
        srts_dict = {}
    else:
        # Open the file, read, and clean.
        with open(out_file, "r") as fp:
            srts_dict = json.load(fp)
        logging.info("Loaded %d mappings." % (len(srts_dict)))
        
        # Set of videos no longer used by KA Lite
        removed_videos = set(srts_dict.keys()) - set([v["youtube_id"] for v in videos.values()])
        if removed_videos:
            logging.info("Removing subtitle information for %d videos (no longer used)." % len(removed_videos))
            for vid in removed_videos:
                del srts_dict[vid]
    logging.info("Querying %d mappings." % (len(videos) - (0 if (force or date_to_check) else len(srts_dict))))

    # 
    n_new_entries = 0
    n_failures = 0
    for video, data in videos.iteritems():
        youtube_id = data['youtube_id']
        if srts_dict.get(youtube_id) and date_to_check:
            # See if we should skip or not, based on 
            last_attempt = srts_dict[youtube_id].get("last_attempt")
            last_attempt = None if not last_attempt else datetime.datetime.strptime(last_attempt, '%Y-%m-%d')
            if last_attempt and date_to_check <= last_attempt:
                logging.debug("Skipping %s for date-check" % youtube_id)
                continue

        elif youtube_id in srts_dict and not force:
            # allow caching of old results, for easy restart
            continue

        try:
            srts_dict[youtube_id] = update_video_entry(youtube_id, entry=srts_dict.get(youtube_id, {}))
        except Exception as e:
            logging.warn("Error updating video %s: %s" % (youtube_id, e))
            n_failures += 1
            continue

        if n_new_entries % frequency_to_save == 0:
            if frequency_to_save > 10:
                logging.info("On loop %d dumping dictionary into %s" %(n_new_entries, out_file))
            with open(out_file, 'wb') as fp:
                json.dump(srts_dict, fp)
        n_new_entries += 1

    # Finished the loop: save and report
    with open(out_file, 'wb') as fp:
        json.dump(srts_dict, fp)
    if n_failures == 0:
        logging.info("Great success! Stored %d fresh entries, %d total." % (n_new_entries, len(srts_dict)))
    else:
        logging.warn("Stored %s fresh entries, but with %s failures." % (n_new_entries, n_failures))


def update_subtitle_map(code_to_check, date_to_check):
    """Update JSON dictionary of subtitle information based on arguments provided"""

    srts_dict = json.loads(open(settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME).read())
    for youtube_id, data in srts_dict.items():
        # ensure response code and date exists
        response_code = data.get("api_response")
        last_attempt = data.get("last_attempt")
        if last_attempt:
            last_attempt = datetime.datetime.strptime(last_attempt, '%Y-%m-%d')

        # HELP: why does the below if statement suck so much? does it suck? it feels like it sucks
        # case: -d AND -s
        flag_for_refresh = True#not (response_code or last_attempt)
        flag_for_refresh = flag_for_refresh and (not date_to_check or date_to_check > last_attempt)
        flag_for_refresh = flag_for_refresh and (not code_to_check or code_to_check == "all" or code_to_check == response_code)
        if not flag_for_refresh:
            continue

        try:
            srts_dict[youtube_id] = update_video_entry(youtube_id, entry=srts_dict[youtube_id])
        except Exception as e:
            logging.warn("Error updating video %s: %s" % (youtube_id, e))


    logging.info("Great success! Re-writing JSON file.")
    with open(settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME, 'wb') as fp:
        json.dump(srts_dict, fp)


def update_video_entry(youtube_id, entry={}):
    """Return a dictionary to be appended to the current schema:
            youtube_id: {
                            "amara_code": "3x4mp1e",
                            "language_codes": ["en", "es", "etc"],
                            "api_response": "success" OR "client_error" OR "server_error",
                            "last_success": "2013-07-06",
                            "last_attempt": "2013-07-06",
                        }
    To update an entry, pass it in.
    """
    request_url = "https://www.amara.org/api2/partners/videos/?format=json&video_url=http://www.youtube.com/watch?v=%s" % (
        youtube_id)
    r = subtitle_utils.make_request(headers, request_url)
    # add api response first to prevent empty json on errors
    entry["last_attempt"] = unicode(datetime.datetime.now().date())

    if isinstance(r, basestring):  # string responses mean some type of error
        logging.info("%s at %s" %(r, request_url))
        entry["api_response"] = r
        return entry

    try:
        content = json.loads(r.content)
        assert "objects" in content  # just index in, to make sure the expected data is there.
        assert len(content["objects"]) == 1
        languages = content["objects"][0]["languages"]
    except Exception as e:
        logging.warn("%s: Could not load json response: %s" % (youtube_id, e))
        entry["api_response"] = "client-error"
        #import pdb; pdb.set_trace()
        return entry

    # Get all the languages
    try:
        prev_languages = entry.get("language_codes")

        entry["language_codes"] = []
        entry["amara_code"] = None
        if languages:
            for language in languages:
                entry["language_codes"].append(language['code'])

            # pull amara video id
            amara_code = languages[0]["subtitles_uri"].split("/")[4]
            assert len(amara_code) == 12  # in case of future API change
            entry["amara_code"] = amara_code

        added_languages = set(entry["language_codes"]) - set(prev_languages)
        removed_languages = set(prev_languages) - set(entry["language_codes"])
        logging.info("Success for id=%s%s%s" % (
            youtube_id,
            "" if not added_languages else "; added languages=%s" % list(added_languages),
            "" if not removed_languages else "; removed languages=%s" % list(removed_languages),
        ))
        entry["api_response"] = "success"
        entry["last_success"] = unicode(datetime.datetime.now().date())

        return entry
    except Exception as e:
        logging.warn("Failed to grab language / amara codes for %s: %s" % (youtube_id, e))
        entry["api_response"] = "client-error"
        #import pdb; pdb.set_trace()
        return entry


def update_language_srt_map():
    """Update the language_srt_map from the api_info_map"""

    # Create file if first time being run
    language_srt_filepath = settings.SUBTITLES_DATA_ROOT + LANGUAGE_SRT_FILENAME
    srt_download_info_filepath = settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME

    if not subtitle_utils.file_already_exists(language_srt_filepath):
        with open(language_srt_filepath, 'w') as outfile:
            json.dump({}, outfile)

    # Load the srt map
    try:
        language_srt_map = json.loads(open(language_srt_filepath).read())
    except Exception as e:
        # Probably corrupted.
        logging.warn("Could not open %s for updates; aborting.  Error=%s" % (language_srt_filepath, e))
        return{}

    # Load the current download status
    try:
        api_info_map = json.loads(open(settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME).read())
    except Exception as e:
        # Must be corrupted; start from scratch!
        logging.warn("Could not open %s for updates; starting from scratch.  Error=%s" % (srt_download_info_filepath, e))
        api_info_map = {}

    # Build old dictionary, to be able to detect removed subtitles
    #   (for example, if they were found to be crap)
    #   Note: Faster to determine past languages up front
    old_api_info_map = {}
    for lang_code, dict in language_srt_map.iteritems():
        for youtube_id in dict.keys():
            if youtube_id not in old_api_info_map:
                old_api_info_map[youtube_id] = {}
                old_api_info_map[youtube_id]["language_codes"] = []
            old_api_info_map[youtube_id]["language_codes"].append(lang_code)

    for youtube_id, content in api_info_map.iteritems():

        # Determining past_languages is very expensive and slow
        cur_languages = set(content.get("language_codes", []))
        past_languages = set(old_api_info_map.get(youtube_id, {}).get("language_codes", []))

        # Remove languages that no longer have subtitles
        for lang_code in (past_languages - cur_languages):
            del language_srt_map[lang_code][youtube_id]

        # Add languages that now have subtitles
        for lang_code in (cur_languages - past_languages):
            if not language_srt_map.get(lang_code):
                # create empty entry for video entry if it doesn't exist
                logging.info("Creating language section '%s'" % lang_code)
                language_srt_map[lang_code] = {}

            # Add any missing entries
            language_srt_map[lang_code][youtube_id] = {
                "downloaded": False,
                "api_response": "",
                "last_attempt": "",
                "last_success": "",
            }

    # Final cleaning to clear any languages with no info
    for lang_code in language_srt_map.keys():
        if not language_srt_map[lang_code]:
            logging.info("Subtitle support for %s has been terminated; removing." % lang_code)
            del language_srt_map[lang_code]

    logging.info("Writing updates to %s" % language_srt_filepath)
    with open(language_srt_filepath, 'wb') as fp:
            json.dump(language_srt_map, fp)

    return language_srt_map


def print_language_availability_table(language_srt_map):
    logging.info("=============================================")
    logging.info("=\tLanguage\t=\tNum Videos\t=")
    for lang_code in sorted(language_srt_map.keys()):
        logging.info("=\t%-8s\t=\t%4d srts\t=" % (lang_code, len(language_srt_map[lang_code])))
    logging.info("=============================================")

    n_srts = sum([len(dict) for dict in language_srt_map.values()])
    logging.info("Great success! Subtitles support found for %d languages, %d total dubbings!" % (len(language_srt_map), n_srts))




class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: %s" % (settings.SUBTITLES_DATA_ROOT + LANGUAGE_SRT_FILENAME)

    option_list = BaseCommand.option_list + (
        # Basic options
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help="Force a new mapping. Cannot be run with other options. Fetches new data for every one of our videos and overwrites current data with fresh data from Amara. Should really only ever be run once, because data can be updated from then on with '-s all'.",
                    metavar="FORCE"),
        make_option('-r', '--response-code',
                    action='store',
                    dest='response_code',
                    default=None,
                    help="Which api-response code to recheck. Can be combined with -d. USAGE: '-r all', '-r client-error', or '-r server-error' (default: None (only download new video info)).",
                    metavar="RESPONSE_CODE"),
        make_option('-d', '--date-since-attempt',
                    action='store',
                    dest='date_since_attempt',
                    default=None,
                    help="Setting a date flag will update only those entries which have not been attempted since that date. Can be combined with -r. This could potentially be useful for updating old subtitles. USAGE: '-d MM/DD/YYYY'"),
    )

    def handle(self, *args, **options):
        #try:
            converted_date = subtitle_utils.convert_date_input(options.get("date_since_attempt"))

            create_all_mappings(force=options.get("force"), frequency_to_save=5, date_to_check=converted_date)
            update_subtitle_map(options.get("response_code"), converted_date)
            logging.info("Executed successfully. Updating language => subtitle mapping to record any changes!")

            language_srt_map = update_language_srt_map()
            print_language_availability_table(language_srt_map)
            logging.info("Process complete.")
        #except Exception as e:
        #    raise CommandError(str(e))