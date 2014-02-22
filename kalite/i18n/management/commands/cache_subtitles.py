"""
CENTRAL SERVER ONLY

This command is used to cache srt files on the central server. It uses
the mapping generate by generate_subtitle_map to make requests of the
Amara API.

NOTE: srt map deals with amara, so uses ietf codes (e.g. en-us). However,
  when directories are created, we use django-style directories (e.g. en_US)
"""
import copy
import datetime
import glob
import json
import requests
import os
import shutil
import sys
import time
import zipfile
from functools import partial
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from i18n import AMARA_HEADERS, LANG_LOOKUP_FILEPATH, LOCALE_ROOT, SRTS_JSON_FILEPATH, SUBTITLES_DATA_ROOT, SUBTITLE_COUNTS_FILEPATH
from i18n import lcode_to_django_dir, lcode_to_ietf, get_language_name, get_lang_map_filepath, get_srt_path, LanguageNotFoundError, get_supported_language_map, get_langs_with_subtitles
from settings import LOG as logging
from utils.general import convert_date_input, ensure_dir, softload_json
from utils.internet import make_request


class LanguageNameDoesNotExist(Exception):

    def __init__(self, lang_code):
        self.lang_code = lang_code

    def __str__(self):
        return "The language name for (%s) doesn't exist yet. Please add it to the lookup dictionary by running the get_all_languages.py script located in utils/" % self.lang_code


def clear_subtitles_cache(lang_codes=None, locale_root=LOCALE_ROOT):
    """
    Language codes will be converted to django format (e.g. en_US)
    """
    lang_codes = lang_codes or get_langs_with_subtitles()
    for lang_code in lang_codes:
        lang_code = lcode_to_ietf(lang_code)

        # Clear the status file
        lm_file = get_lang_map_filepath(lang_code)
        download_status = softload_json(lm_file, raises=True)
        for key in download_status:
            download_status[key] = {u'downloaded': False, u'last_success': u'', u'last_attempt': u'', u'api_response': u''}
        with open(lm_file, "w") as fp:
            json.dump(download_status, fp)

        # Delete all srt files
        srt_path = get_srt_path(lang_code)
        if os.path.exists(srt_path):
            shutil.rmtree(srt_path)


def get_all_prepped_lang_codes():
    """Pre-prepped language codes, for downloading srts"""
    lang_codes = []
    for filename in get_all_download_status_files():
        lang_code = os.path.basename(filename).split("_")[0]
        lang_codes.append(lcode_to_ietf(lang_code))
    return lang_codes


def download_srt_from_3rd_party(lang_codes=None, **kwargs):
    """Download subtitles specified by command line args"""

    lang_codes = lang_codes or get_all_prepped_lang_codes()
    bad_languages = {}

    for lang_code in lang_codes:
        lang_code = lcode_to_ietf(lang_code)
        lang_code = get_supported_language_map(lang_code)['amara']

        try:
            lang_map_filepath = get_lang_map_filepath(lang_code)
            if not os.path.exists(lang_map_filepath):
                videos = {}  # happens if an unknown set for subtitles.
            else:
                with open(lang_map_filepath, "r") as fp:
                    videos = json.load(fp)
        except Exception as e:
            error_msg = "Error in subtitles metadata file for %s: %s" % (lang_code, e)
            logging.error(error_msg)
            bad_languages[lang_code] = error_msg
            continue

        try:
            download_if_criteria_met(videos, lang_code=lang_code, **kwargs)
        except Exception as e:
            error_msg = "Error downloading subtitles for %s: %s" % (lang_code, e)
            logging.error(error_msg)
            bad_languages[lang_code] = error_msg
            continue

    # now report final results
    if bad_languages:
        outstr = "Failed to download subtitles for the following languages: %s" % (bad_languages.keys())
        outstr += "\n" + str(bad_languages)
        logging.error(outstr)


def get_all_download_status_files():
    """Return filenames in data/subtitles/languages/ that contain download status information"""
    languages_dir = glob.glob(os.path.join(SUBTITLES_DATA_ROOT, "languages", "*_download_status.json"))
    return languages_dir


def download_if_criteria_met(videos, lang_code, force, response_code, date_since_attempt, frequency_to_save, *args, **kwargs):
    """Execute download of subtitle if it meets the criteria specified by the command line args

    Note: videos are a dict; keys=youtube_id, values=data
    Note: lang_code is in IETF format.
    """
    date_specified = convert_date_input(date_since_attempt)

    # Filter up front, for efficiency (& reporting's sake)
    n_videos = len(videos)

    logging.info("There are (up to) %s total videos with subtitles for language '%s'.  Let's go get them!" % (
        n_videos, lang_code,
    ))

    # Filter based on response code
    if response_code and response_code != "all":
        logging.info("Filtering based on response code (%s)..." %
                     response_code)
        response_code_filter = partial(
            lambda vid, rcode: rcode == vid["api_response"], rcode=response_code)
        videos = dict([(k, v) for k, v in videos.iteritems() if response_code_filter(v)])
        logging.info("%4d of %4d videos match your specified response code (%s)" % (
            len(videos), n_videos, response_code,
        ))

    if date_specified:
        logging.info("Filtering based on date...")
        for k in videos.keys():
            if not videos[k]["last_attempt"]:
                continue
            elif datetime.datetime.strptime(videos[k]["last_attempt"], '%Y-%m-%d') < date_specified:
                continue
            elif False:  # TODO(bcipolli): check output filename exists, as per # 1359
                continue
            else:
                del videos[k]

        logging.info("%4d of %4d videos need refreshing (last refresh more recent than %s)" % (
            len(videos), n_videos, date_specified,
        ))

    # Loop over videos needing refreshing
    n_loops = 0
    srt_count = None
    for youtube_id, entry in videos.items():
        previously_downloaded = entry.get("downloaded")

        if previously_downloaded and not force:
            logging.info("Already downloaded %s/%s. To redownload, run again with -f." % (
                lang_code, youtube_id,
            ))
            continue

        logging.debug("Attempting to download subtitle for lang: %s and YouTube ID: %s" % (
            lang_code, youtube_id,
        ))
        response = download_subtitle(youtube_id, lang_code, format="srt")
        time_of_attempt = unicode(datetime.datetime.now().date())

        if response in ["client-error", "server-error", "unexpected_error"]:
            # Couldn't download
            logging.info("%s/%s.srt: Updating JSON file to record error (%s)." % (
                lang_code, youtube_id, response,
            ))
            update_json(youtube_id, lang_code, previously_downloaded, response, time_of_attempt)

        else:
            dirpath = get_srt_path(lang_code)
            fullpath = os.path.join(dirpath, youtube_id + ".srt")
            ensure_dir(dirpath)

            logging.debug("Writing file to %s" % fullpath)
            with open(fullpath, 'w') as fp:
                fp.write(response.encode('UTF-8'))

            logging.info("%s/%s.srt: Updating JSON file to record success." % (
                lang_code, youtube_id,
            ))
            update_json(youtube_id, lang_code, True, "success", time_of_attempt)

        # Update srt availability mapping
        n_loops += 1
        if n_loops % frequency_to_save == 0 or n_loops == len(videos.keys()):
            srt_count = store_new_counts(lang_code=lang_code)
            logging.info("%s: On loop %d / %d, stored: subtitle count = %d." % (
                lang_code, n_loops, len(videos), srt_count,
            ))

    # Summarize output
    if srt_count is None:
        # only none if nothing was done.
        logging.info("Nothing was done.")
    else:
        logging.info("We now have %d subtitles (amara thought they had %d) for language '%s'!" % (
            srt_count, n_videos, lang_code,
        ))


def download_subtitle(youtube_id, lang_code, format="srt"):
    """
    Return subtitles for YouTube ID in language specified. Return False if they do not exist. Update local JSON accordingly.

    Note: srt map deals with amara, so uses lower-cased ietf codes (e.g. en-us)
    """
    assert format == "srt", "We only support srt download at the moment."


    # srt map deals with amara, so uses ietf codes (e.g. en-us)
    api_info_map = softload_json(SRTS_JSON_FILEPATH, raises=True)

    # get amara id
    amara_code = api_info_map.get(youtube_id, {}).get("amara_code")

    # make request
    # Please see http://amara.readthedocs.org/en/latest/api.html
    base_url = "https://amara.org/api2/partners/videos"

    resp = make_request(AMARA_HEADERS, "%s/%s/languages/%s/subtitles/?format=srt" % (
        base_url, amara_code, lang_code.lower(),
    ))
    if isinstance(resp, basestring):
        return resp
    else:
        # return the subtitle text, replacing empty subtitle lines with
        # spaces to make the FLV player happy
        try:
            resp.encoding = "UTF-8"
            response = (resp.text or u"") \
                .replace("\n\n\n", "\n   \n\n") \
                .replace("\r\n\r\n\r\n", "\r\n   \r\n\r\n")
        except Exception as e:
            logging.error(e)
            response = "client-error"
        return response


def update_json(youtube_id, lang_code, downloaded, api_response, time_of_attempt):
    """Update language_srt_map to reflect download status

    lang_code in IETF format
    """
    # Open JSON file
    filepath = get_lang_map_filepath(lang_code)
    language_srt_map = softload_json(filepath, logger=logging.error)
    if not language_srt_map:
        return False

    # create updated entry
    entry = language_srt_map[youtube_id]
    entry["downloaded"] = downloaded
    entry["api_response"] = api_response
    entry["last_attempt"] = time_of_attempt
    if api_response == "success":
        entry["last_success"] = time_of_attempt

    # update full-size JSON with new information
    language_srt_map[youtube_id].update(entry)

    # write it to file
    json_file = open(filepath, "wb")
    json_file.write(json.dumps(language_srt_map))
    json_file.close()
    logging.debug("File updated.")

    return True


def store_new_counts(lang_code, data_path=SUBTITLES_DATA_ROOT, locale_root=LOCALE_ROOT):
    """Write a new dictionary of srt file counts in respective download folders"""
    language_subtitle_count = {}
    subtitles_path = get_srt_path(lang_code)
    lang_name = get_language_name(lang_code)

    try:
        count = len(glob.glob("%s/*.srt" % subtitles_path))

        language_subtitle_count[lang_name] = {}
        language_subtitle_count[lang_name]["count"] = count
        language_subtitle_count[lang_name]["code"] = lang_code
    except LanguageNameDoesNotExist as ldne:
        count = 0
        logging.debug(ldne)
    except:
        count = 0
        logging.info("%-4s subtitles for %-20s" % ("No", lang_name))

    # Always write to disk.
    write_count_to_json(language_subtitle_count, data_path)

    return count


def write_count_to_json(subtitle_counts, data_path):
    """Write JSON to file in static/data/subtitles/"""
    current_counts = softload_json(SUBTITLE_COUNTS_FILEPATH, logger=logging.error)
    current_counts.update(subtitle_counts)

    logging.debug("Writing fresh srt counts to %s" % SUBTITLE_COUNTS_FILEPATH)
    with open(SUBTITLE_COUNTS_FILEPATH, 'wb') as fp:
        # sort here, so we don't have to sort later when seving to clients
        json.dump(current_counts, fp, sort_keys=True)


def validate_language_map(lang_codes):
    """
    This function will tell you any blockers that you'll hit while
    running this command.

    All srt languages must exist in the language map; missing languages
    will cause errors during command running (which can be long).
    This function avoids that problem by doing the above consistency check.
    """
    lang_codes = lang_codes or get_all_prepped_lang_codes()
    missing_langs = []
    for lang_code in lang_codes:
        try:
            get_language_name(lcode_to_ietf(lang_code), error_on_missing=True)
        except LanguageNotFoundError:
            missing_langs.append(lang_code)

    if missing_langs:
        logging.warn("Please add the following language codes to %s:\n\t%s" % (
            LANG_LOOKUP_FILEPATH, missing_langs,
        ))

class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitles/srts_download_status.json"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=None,
                    metavar="LANG_CODE",
                    help="Specify a particular language code (e.g. en-us) to download subtitles for. Can be used with -f to update previously downloaded subtitles."),
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    metavar="FORCE",
                    help="Force re-downloading of previously downloaded subtitles to refresh the repo. Can be used with -l. Default behavior is to not re-download subtitles we already have."),
        make_option('-d', '--date_since_attempt',
                    action='store',
                    dest='date_since_attempt',
                    default=None,
                    metavar="DATE",
                    help="Setting a date flag will update only those entries which have not been attempted since that date. Can be combined with -r. This could potentially be useful for updating old subtitles. USAGE: '-d MM/DD/YYYY'."),
        make_option('-r', '--response-code',
                    action='store',
                    dest='response_code',
                    default="",
                    metavar="RESP_CODE",
                    help="Which api-response code to recheck. Can be combined with -d. USAGE: '-r success', '-r client-error',  '-r server-error', or '-r all'  Default: -r (empty)"),
        make_option('-s', '--frequency_to_save',
                    action='store',
                    dest='frequency_to_save',
                    default=5,
                    metavar="FREQ_SAVE",
                    help="How often to update the srt availability status file. The script will go FREQ_SAVE loops before saving a new master file"),
    )


    def handle(self, *args, **options):
        if not settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the central server.")

        # None represents all
        lang_codes = [lcode_to_ietf(options["lang_code"])] if options["lang_code"] else None
        del options["lang_code"]

        if len(args) > 1:
            raise CommandError("Max 1 arg")

        elif len(args) == 1:
            if args[0] == "clear":
                logging.info("Clearing subtitles...")
                clear_subtitles_cache(lang_codes)

            else:
                raise CommandError("Unknown argument: %s" % args[0])

        else:
            validate_language_map(lang_codes)

            logging.info("Downloading...")
            download_srt_from_3rd_party(lang_codes=lang_codes, **options)

            validate_language_map(lang_codes)  # again at the end, so output is visible

            # for compatibility with KA Lite versions less than 0.10.3
            for lang in (lang_codes or get_langs_with_subtitles()):
                generate_srt_availability_file(lang)

        logging.info("Process complete.")


def generate_srt_availability_file(lang_code):
    '''
    For compatibility with versions less than 0.10.3, we need to generate this
    json file that contains the srts for the videos.
    '''

    # this path is a direct copy of the path found in the old function that generated this file
    srts_file_dest_path = os.path.join(settings.STATIC_ROOT, 'data', 'subtitles', 'languages', "%s_available_srts.json") % lang_code
    ensure_dir(os.path.dirname(srts_file_dest_path))

    srts_path = get_srt_path(lang_code) # not sure yet about this; change once command is complete
    try:
        files = os.listdir(srts_path)
    except OSError:             # directory doesnt exist or we cant read it
        files = []

    yt_ids = [f.rstrip(".srt") for f in files]
    srts_dict = { 'srt_files': yt_ids }

    with open(srts_file_dest_path, 'wb') as fp:
        logging.debug('Creating %s', srts_file_dest_path)
        json.dump(srts_dict, fp)

    return yt_ids
