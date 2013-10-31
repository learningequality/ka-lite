"""
This command is used to cache srt files on the central server. It uses 
the mapping generate by generate_subtitle_map to make requests of the 
Amara API. 
"""

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
from generate_subtitle_map import SRTS_JSON_FILENAME, headers, get_lang_map_filepath
from settings import LOG as logging
from shared.i18n import get_language_name, convert_language_code_format
from utils.general import convert_date_input, ensure_dir, make_request


LOCALE_ROOT = os.path.join(settings.LOCALE_PATHS[0])


class LanguageNameDoesNotExist(Exception):

    def __init__(self, lang_code):
        self.lang_code = lang_code

    def __str__(self):
        return "The language name for (%s) doesn't exist yet. Please add it to the lookup dictionary by running the get_all_languages.py script located in utils/" % self.lang_code


def clear_subtitles_cache(language_codes=None, locale_root=LOCALE_ROOT):
    language_codes = language_codes or os.listdir(locale_root)
    for language_code in language_codes:

        # Clear the status file
        lm_file = get_lang_map_filepath(language_code)
        with open(lm_file, "r") as fp:
            download_status = json.load(fp)
        for key in download_status:
            download_status[key] = {u'downloaded': False, u'last_success': u'', u'last_attempt': u'', u'api_response': u''}
        with open(lm_file, "w") as fp:
            json.dump(download_status, fp)

        # Delete all srt files
        srt_path = get_srt_path(language_code)
        if os.path.exists(srt_path):
            shutil.rmtree(srt_path)


def download_srt_from_3rd_party(*args, **kwargs):
    """Download subtitles specified by command line args"""

    lang_code = kwargs.get("lang_code", None)

    # if language specified, do those, if not do all
    if not lang_code:
        raise CommandError("You must specify a language code or 'all' with -l")
    elif lang_code == "all":
        for filename in get_all_download_status_files():
            try:
                videos = json.loads(open(filename).read())
            except Exception as e:
                logging.error(e)
                raise CommandError("Unable to open %s. The file might be corrupted. Please re-run the generate_subtitle_map command to regenerate it." % filename)
            
            try:
                kwargs["lang_code"] = os.path.basename(filename).split("_")[0]
                download_if_criteria_met(videos, *args, **kwargs)
            except Exception as e:
                logging.error(e)
                raise CommandError("Error while downloading language srts: %s" % e)
    else: 
        srt_list_path = get_lang_map_filepath(convert_language_code_format(lang_code))
        try:
            videos = json.loads(open(srt_list_path).read())
        except:
            logging.warning("No subtitles available for download for language code %s. Skipping." % lang_code)
        else:
            download_if_criteria_met(videos, *args, **kwargs)


def get_srt_path(lang_code, locale_root=LOCALE_ROOT):
    return os.path.join(locale_root, lang_code, "subtitles/")

def get_all_download_status_files():
    """Return filenames in data/subtitles/languages/ that contain download status information"""
    languages_dir = glob.glob(os.path.join(settings.SUBTITLES_DATA_ROOT, "languages/", "*_download_status.json"))
    return languages_dir


def download_if_criteria_met(videos, lang_code, force, response_code, date_since_attempt, frequency_to_save, *args, **kwargs):
    """Execute download of subtitle if it meets the criteria specified by the command line args

    Note: videos are a dict; keys=youtube_id, values=data
    """
    date_specified = convert_date_input(date_since_attempt)

    # Filter up front, for efficiency (& reporting's sake)
    n_videos = len(videos)

    logging.info("There are (up to) %s total videos with subtitles for language '%s'.  Let's go get them!" % (n_videos, lang_code))

    # Filter based on response code
    if response_code and response_code != "all":
        logging.info("Filtering based on response code (%s)..." %
                     response_code)
        response_code_filter = partial(
            lambda vid, rcode: rcode == vid["api_response"], rcode=response_code)
        videos = dict([(k, v)
                      for k, v in videos.items() if response_code_filter(v)])
        logging.info("%4d of %4d videos match your specified response code (%s)" %
                     (len(videos), n_videos, response_code))

    if date_specified:
        logging.info("Filtering based on date...")
        for k, v in videos.items():
            if not v["last_attempt"] or datetime.datetime.strptime(v["last_attempt"], '%Y-%m-%d') < date_specified:
                continue
            else:
                del videos[k]

        logging.info("%4d of %4d videos need refreshing (last refresh more recent than %s)" %
                     (len(videos), n_videos, date_specified))

    # Loop over good videos
    n_loops = 0
    for youtube_id, entry in videos.items():
        previously_downloaded = entry.get("downloaded")

        if previously_downloaded and not force:
            logging.info("Already downloaded %s/%s. To redownload, run again with -R." %
                         (lang_code, youtube_id))
            continue

        logging.info("Attempting to download subtitle for lang: %s and YouTube ID: %s" %
                     (lang_code, youtube_id))
        response = download_subtitle(youtube_id, lang_code, format="srt")
        time_of_attempt = unicode(datetime.datetime.now().date())

        if response == "client-error" or response == "server-error":
            # Couldn't download
            logging.info("Updating JSON file to record %s." % response)
            update_json(youtube_id, lang_code, previously_downloaded, response, time_of_attempt)

        else:
            dirpath = get_srt_path(lang_code)
            filename = youtube_id + ".srt"
            fullpath = dirpath + filename
            logging.info("Writing file to %s" % fullpath)

            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            with open(fullpath, 'w') as fp:
                fp.write(response.encode('UTF-8'))

            logging.info("Updating JSON file to record success.")
            update_json(youtube_id, lang_code, True, "success", time_of_attempt)

        # Update srt availability mapping
        n_loops += 1
        if n_loops % frequency_to_save == 0 or n_loops == len(videos.keys())-1:
            logging.info(
                "On loop %d - generating new subtitle counts!" % n_loops)
            get_new_counts(language_code=lang_code)

    srt_availability = get_new_counts(language_code=lang_code)

    # Summarize output
    logging.info("We now have %d subtitles (amara thought they had %d) for language '%s'!" % (srt_availability, n_videos, lang_code))


def download_subtitle(youtube_id, lang_code, format="srt"):
    """Return subtitles for YouTube ID in language specified. Return False if they do not exist. Update local JSON accordingly."""
    assert format == "srt", "We only support srt download at the moment."

    api_info_map = json.loads(
        open(settings.SUBTITLES_DATA_ROOT + SRTS_JSON_FILENAME).read()
    )
    # get amara id
    amara_code = api_info_map.get(youtube_id).get("amara_code")

    # make request
    # Please see http://amara.readthedocs.org/en/latest/api.html
    base_url = "https://amara.org/api2/partners/videos"

    r = make_request(headers, "%s/%s/languages/%s/subtitles/?format=srt" % (
        base_url, amara_code, lang_code))
    if isinstance(r, basestring):
        return r
    else:
        # return the subtitle text, replacing empty subtitle lines with
        # spaces to make the FLV player happy
        try:
            r.encoding = "UTF-8"
            response = (r.text or u"") \
                .replace("\n\n\n", "\n   \n\n") \
                .replace("\r\n\r\n\r\n", "\r\n   \r\n\r\n")
        except Exception as e:
            logging.error(e)
            response = "client-error"
        return response


def update_json(youtube_id, lang_code, downloaded, api_response, time_of_attempt):
    """Update language_srt_map to reflect download status"""
    # Open JSON file
    filepath = get_lang_map_filepath(lang_code)
    try: 
        language_srt_map = json.loads(open(filepath).read())
    except Exception as e:
        logging.error("Something went wrong while trying to open the json file (%s): %s" % (filepath, e))
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
    logging.info("File updated.")
    json_file = open(filepath, "wb")
    json_file.write(json.dumps(language_srt_map))
    json_file.close()
    return True


def get_new_counts(language_code, data_path=settings.SUBTITLES_DATA_ROOT, locale_root=LOCALE_ROOT):
    """Write a new dictionary of srt file counts in respective download folders"""
    language_subtitle_count = {}
    subtitles_path = get_srt_path(language_code)
    lang_name = get_language_name(language_code)

    try:
        count = len(glob.glob("%s/*.srt" % subtitles_path))
        logging.info("%4d subtitles for %-20s" % (count, lang_name))

        language_subtitle_count[lang_name] = {}
        language_subtitle_count[lang_name]["count"] = count
        language_subtitle_count[lang_name]["code"] = language_code
    except LanguageNameDoesNotExist as ldne:
        logging.warn(ldne)
    except:
        logging.info("%-4s subtitles for %-20s" % ("No", lang_name))

    write_new_json(language_subtitle_count, data_path)
    return language_subtitle_count[lang_name].get("count")


def write_new_json(subtitle_counts, data_path):
    """Write JSON to file in static/data/subtitles/"""
    filename = "subtitle_counts.json"
    filepath = data_path + filename
    try:
        current_counts = json.loads(open(filepath).read())
    except Exception as e:
        logging.error("Subtitle counts file appears to be corrupted (%s). Starting from scratch." % e)
        current_counts = {}
    current_counts.update(subtitle_counts)
    logging.info("Writing fresh srt counts to %s" % filepath)
    with open(filepath, 'wb') as fp:
        json.dump(current_counts, fp)


class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitles/srts_download_status.json"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=None,
                    metavar="LANG_CODE",
                    help="Specify a particular language code to download subtitles for. Can be used with -R to update previously downloaded subtitles."),
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
        lang_codes = [options["lang_code"]] if options["lang_code"] else None

        if len(args) == 1:
            if args[0] == "clear":
                logging.info("Clearing subtitles...")
                clear_subtitles_cache(lang_codes)
            else:
                raise CommandError("Unknown argument: %s" % args[0])

        elif len(args) > 1:
            raise CommandError("Max 1 arg")

        else:

            logging.info("Downloading...")
            download_srt_from_3rd_party(**options)

            logging.info("Process complete.")
