"""
CENTRAL SERVER ONLY

Command used to cache data from Amara's API about which languages videos
have been subtitled in. This data is then used by the command cache_subtitles
to intelligently request srt files from Amara's API, rather than blindly requesting
tons of srt files that don't exist. This command should be run infrequently, but
regularly, to ensure we are at least putting in requests for the srts that exist.

NOTE: srt map deals with amara, so uses ietf codes (e.g. en-us).
"""

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
from shared.i18n import AMARA_HEADERS, SRTS_JSON_FILEPATH
from shared.i18n import get_language_name, get_lang_map_filepath, lcode_to_ietf
from shared.topic_tools import get_slug2id_map
from utils.general import convert_date_input, ensure_dir, make_request


class OutDatedSchema(Exception):
    def __str__(self):
        return "The current data schema is outdated and doesn't store the important bits. Please run 'generate_subtitles_map.py -f' to generate a totally new file and the correct schema."


def create_all_mappings(force=False, frequency_to_save=100, response_to_check=None, date_to_check=None, map_file=SRTS_JSON_FILEPATH):
    """
    Write or update JSON file that maps from YouTube ID to Amara code and languages available.

    This command updates the json file that records what languages videos have been subtitled in.
    It loops through all video ids, records a list of which languages Amara says it has been subtitled in
    and meta data about the request (e.g. date, response code).

    See the schema in the docstring for fcn update_video_entry.
    """
    youtube_ids = get_slug2id_map().values()

    # Initialize the data
    if not os.path.exists(map_file):
        ensure_dir(os.path.dirname(map_file))
        srts_dict = {}
    else:
        # Open the file, read, and clean out old videos.
        try:
            with open(map_file, "r") as fp:
                srts_dict = json.load(fp)
        except Exception as e:
            if not force:  # only handle the error if force=True.  Otherwise, these data are too valuable to lose, so just assume a temp problem.
                raise
            else:
                logging.error("JSON file corrupted, using empty json and starting from scratch (%s)" % e)
                srts_dict = {}
        else:
            logging.info("Loaded %d mappings." % (len(srts_dict)))

        # Set of videos no longer used by KA Lite
        removed_videos = set(srts_dict.keys()) - set(youtube_ids)
        if removed_videos:
            logging.info("Removing subtitle information for %d videos (no longer used)." % len(removed_videos))
            for vid in removed_videos:
                del srts_dict[vid]
    logging.info("Querying %d mappings." % (len(youtube_ids) - (0 if (force or date_to_check) else len(srts_dict))))

    # Once we have the current mapping, proceed through logic to update the mapping
    n_new_entries = 0
    n_failures = 0
    for youtube_id in youtube_ids:
        # Decide whether or not to update this video based on the arguments provided at the command line
        cached = youtube_id in srts_dict
        if not force and cached:
            # First, check against date
            flag_for_refresh = True # not (response_code or last_attempt)
            last_attempt = srts_dict[youtube_id].get("last_attempt")
            last_attempt = None if not last_attempt else datetime.datetime.strptime(last_attempt, '%Y-%m-%d')
            flag_for_refresh = flag_for_refresh and (not date_to_check or date_to_check > last_attempt)
            if not flag_for_refresh:
                logging.debug("Skipping %s for date-check" % youtube_id)
                continue
            # Second, check against response code
            response_code = srts_dict[youtube_id].get("api_response")
            flag_for_refresh = flag_for_refresh and (not response_to_check or response_to_check == "all" or response_to_check == response_code)
            if not (flag_for_refresh):
                logging.debug("Skipping %s for response-code" % youtube_id)
                continue
            if not response_to_check and not date_to_check and cached: # no flags specified and already cached - skip
                logging.debug("Skipping %s for already-cached and no flags specified" % youtube_id)
                continue
        else:
            if force and not cached:
                logging.debug("Updating %s because force flag (-f) given and video not cached." % youtube_id)
            elif force and cached:
                logging.debug("Updating %s because force flag (-f) given. Video was previously cached." % youtube_id)
            else:
                logging.debug("Updating %s because video not yet cached." % youtube_id)

        # If it makes it to here without hitting a continue, then update the entry
        try:
            srts_dict[youtube_id] = update_video_entry(youtube_id, entry=srts_dict.get(youtube_id, {}))
        except Exception as e:
            logging.warn("Error updating video %s: %s" % (youtube_id, e))
            n_failures += 1
            continue

        if n_new_entries % frequency_to_save == 0:
            logging.info("On loop %d dumping dictionary into %s" % (n_new_entries, map_file))
            with open(map_file, 'wb') as fp:
                json.dump(srts_dict, fp)
        n_new_entries += 1

    # Finished the loop: save and report
    with open(map_file, 'wb') as fp:
        json.dump(srts_dict, fp)
    if n_failures == 0:
        logging.info("Great success! Stored %d fresh entries, %d total." % (n_new_entries, len(srts_dict)))
    else:
        logging.warn("Stored %s fresh entries, but with %s failures." % (n_new_entries, n_failures))


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

    Note: language_codes are in IETF format (e.g. en-US)
    """
    request_url = "https://www.amara.org/api2/partners/videos/?format=json&video_url=http://www.youtube.com/watch?v=%s" % (
        youtube_id)
    r = make_request(AMARA_HEADERS, request_url)
    # add api response first to prevent empty json on errors
    entry["last_attempt"] = unicode(datetime.datetime.now().date())

    if isinstance(r, basestring):  # string responses mean some type of error
        logging.info("%s at %s" % (r, request_url))
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
        return entry

    # Get all the languages
    try:
        prev_languages = entry.get("language_codes") or []

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
        return entry


def update_language_srt_map(map_file=SRTS_JSON_FILEPATH):
    """
    Translate the srts_remote_availability dictionary into language specific files
    that can be used by the cache_subtitles command.

    Note: srt map deals with amara, so uses ietf codes (e.g. en-us)
    """
    # Load the current download status
    try:
        with open(map_file) as fp:
            api_info_map = json.load(fp)
    except Exception as e:
        # Must be corrupted; start from scratch!
        logging.warn("Could not open %s for updates; starting from scratch.  Error=%s" % (map_file, e))
        api_info_map = {}

    # Next we want to iterate through those and create a big srt dictionary organized by language code
    remote_availability_map = {}
    for youtube_id, data in api_info_map.items():
        languages = data.get("language_codes", [])
        for lang_code in languages:
            lang_code = lcode_to_ietf(lang_code)
            if not lang_code in remote_availability_map:
                #logging.info("Creating language section '%s'" % lang_code)
                remote_availability_map[lang_code] = {}
            # This entry will be valid if it's new, otherwise it will be overwitten later
            remote_availability_map[lang_code][youtube_id] = {
                "downloaded": False,
                "api_response": "",
                "last_attempt": "",
                "last_success": "",
            }

    # Finally we need to iterate through that dictionary and create individual files for each language code
    for lang_code, new_data in remote_availability_map.items():

        # Try to open previous language file
        lang_map_filepath = get_lang_map_filepath(lang_code)
        if not os.path.exists(lang_map_filepath):
            lang_map = {}
        else:
            try:
                with open(lang_map_filepath, "r") as fp:
                    lang_map = json.load(fp)
            except Exception as e:
                logging.error("Language download status mapping for (%s) is corrupted (%s), rewriting it." % (lang_code, e))
                lang_map = {}

        # First, check to see if it's empty (e.g. no subtitles available for any videos)
        if not new_data:
            logging.info("Subtitle support for %s has been terminated; removing." % lang_code)
            if os.path.exists(lang_map_filepath):
                os.remove(lang_map_filepath)
            continue

        # Compare how many empty entries you are adding and add them to master map
        old_yt_ids = set(new_data.keys())
        new_yt_ids = set(lang_map.keys())
        yt_ids_to_add = set(new_data.keys()) - set(lang_map.keys())
        yt_ids_to_delete = set(lang_map.keys()) - set(new_data.keys())

        if yt_ids_to_add:
            logging.info("Adding %d new YouTube IDs to language (%s)" % (len(yt_ids_to_add), lang_code))
            for yt_id in yt_ids_to_add:
                lang_map[yt_id] = new_data.get(yt_id)

        if yt_ids_to_delete:
            logging.info("Deleting %d old YouTube IDs from language (%s) because they are no longer supported." % (len(yt_ids_to_delete), lang_code))
            for yt_id in yt_ids_to_delete:
                lang_map.pop(yt_id, None)

        # Write the new file to the correct location
        logging.debug("Writing %s" % lang_map_filepath)
        ensure_dir(os.path.dirname(lang_map_filepath))
        with open(lang_map_filepath, 'w') as outfile:
            json.dump(lang_map, outfile)

        # Update the big mapping with the most accurate numbers
        remote_availability_map[lang_code].update(lang_map)

    # Finally, remove any files not found in the current map at all.
    if lang_map_filepath:
        for filename in os.listdir(os.path.dirname(lang_map_filepath)):
            lang_code = lang_code = filename.split("_")[0]
            if not lang_code in remote_availability_map:
                file_to_remove = get_lang_map_filepath(lang_code)
                logging.info("Subtitle support for %s has been terminated; removing." % lang_code)
                if os.path.exists(file_to_remove):
                    os.remove(file_to_remove)
                else:
                    logging.warn("Subtitles metadata for %s not found; skipping deletion of non-existent file %s." % (lang_code, file_to_remove))

    return remote_availability_map


def print_language_availability_table(language_srt_map):
    """
    Prints the # of srts available for each known language code.

    Note: srt map deals with amara, so uses ietf codes (e.g. en-US)
    """

    logging.info("=============================================")
    logging.info("=\tLanguage\t=\tNum Videos\t=")
    for lang_code in sorted(language_srt_map.keys()):
        logging.info("=\t%-8s\t=\t%4d srts\t=" % (lang_code, len(language_srt_map[lang_code])))
    logging.info("=============================================")

    n_srts = sum([len(dict) for dict in language_srt_map.values()])
    logging.info("Great success! Subtitles support found for %d languages, %d total dubbings!" % (
        len(language_srt_map), n_srts,
    ))

class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: %s" % (
        get_lang_map_filepath("<lang_code>"),
    )

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
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")

        converted_date = convert_date_input(options.get("date_since_attempt"))
        create_all_mappings(force=options.get("force"), frequency_to_save=5, response_to_check=options.get("response_code"), date_to_check=converted_date)
        logging.info("Executed successfully. Updating language => subtitle mapping to record any changes!")

        language_srt_map = update_language_srt_map()
        print_language_availability_table(language_srt_map)
        logging.info("Process complete.")
