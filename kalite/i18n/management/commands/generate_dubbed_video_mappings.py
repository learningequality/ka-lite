"""
Command to import mappings from spreadsheet, convert to a json dictionary.
"""
import csv
import datetime
import json
import os
import requests
from optparse import make_option
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError

import settings
from i18n import DUBBED_VIDEOS_MAPPING_FILEPATH
from main.topic_tools import get_node_cache
from settings import LOG as logging
from utils.general import ensure_dir, datediff


SPREADSHEET_ID ="0AhvqOn88FUVedEJXM1ZhMG1XdGJuVTE4OEZ3WkNxYUE"
SPREADSHEET_EXPORT_FORMAT = "csv"
SPREADSHEET_GID = 0
SPREADSHEET_BASE_URL = "https://docs.google.com/spreadsheet/ccc"

def generate_dubbed_video_mappings(download_url=None, csv_data=None):
    """
    Function to do the heavy lifting in getting the dubbed videos map.

    Could be moved into utils
    """
    if not download_url:
        download_url = SPREADSHEET_BASE_URL
        params = {'key': SPREADSHEET_ID, 'gid': SPREADSHEET_GID, 'output': SPREADSHEET_EXPORT_FORMAT}
    else:
        params = {}

    if not csv_data:
        logging.info("Downloading dubbed video data from %s" % download_url)
        response = requests.get(download_url, params=params)
        if response.status_code != 200:
            raise CommandError("Failed to download dubbed video CSV data: status=%s" % response.status)
        csv_data = response.content

    # This CSV file is in standard format: separated by ",", quoted by '"'
    logging.info("Parsing csv file.")
    reader = csv.reader(StringIO(csv_data))

    # Build a two-level video map.
    #   First key: language name
    #   Second key: english youtube ID
    #   Value: corresponding youtube ID in the new language.
    video_map = {}

    row_num = -1
    try:
        # Loop through each row in the spreadsheet.
        while (True):
            row_num += 1
            row = reader.next()


            if row_num < 4:
                # Rows 1-4 are crap.
                continue

            elif row_num == 4:
                # Row 5 is the header row.
                header_row = [v.lower() for v in row]  # lcase all header row values (including language names)
                slug_idx = header_row.index("titled id")
                english_idx = header_row.index("english")
                assert slug_idx != -1, "Video slug column header should be found."
                assert english_idx != -1, "English video column header should be found."

            else:
                # Rows 6 and beyond are data.
                assert len(row) == len(header_row), "Values line length equals headers line length"

                # Grab the slug and english video ID.
                video_slug = row[slug_idx]
                english_video_id = row[english_idx]
                assert english_video_id, "English Video ID should not be empty"
                assert video_slug, "Slug should not be empty"

                # English video is the first video ID column,
                #   and following columns (until the end) are other languages.
                # Loop through those columns and, if a video exists,
                #   add it to the dictionary.
                for idx in range(english_idx, len(row)):
                    if not row[idx]:  # make sure there's a dubbed video
                        continue

                    lang = header_row[idx]
                    if lang not in video_map:  # add the first level if it doesn't exist
                        video_map[lang] = {}
                    dubbed_youtube_id = row[idx]
                    if english_video_id == dubbed_youtube_id and lang != "english":
                        logging.error("Removing entry for (%s, %s): dubbed and english youtube ID are the same." % (lang, english_video_id))
                    #elif dubbed_youtube_id in video_map[lang].values():
                        # Talked to Bilal, and this is actually supposed to be OK.  Would throw us for a loop!
                        #    For now, just keep one.
                        #for key in video_map[lang].keys():
                        #    if video_map[lang][key] == dubbed_youtube_id:
                        #        del video_map[lang][key]
                        #        break
                        #logging.error("Removing entry for (%s, %s): the same dubbed video ID is used in two places, and we can only keep one in our current system." % (lang, english_video_id))
                    else:
                        video_map[lang][english_video_id] = row[idx]  # add the corresponding video id for the video, in this language.

    except StopIteration:
        # The loop ends when the CSV file hits the end and throws a StopIteration
        pass

    # Now, validate the mappings with our topic data
    known_videos = get_node_cache("Video").keys()
    missing_videos = set(known_videos) - set(video_map["english"].keys())
    extra_videos = set(video_map["english"].keys()) - set(known_videos)
    if missing_videos:
        logging.warn("There are %d known videos not in the list of dubbed videos" % len(missing_videos))
        logging.warn("Adding missing English videos to English dubbed video map")
        for video in missing_videos:
            video_map["english"][video] = video
    if extra_videos:
        logging.warn("There are %d videos in the list of dubbed videos that we have never heard of." % len(extra_videos))

    return (video_map, csv_data)


class Command(BaseCommand):
    help = "Make a dictionary of english video=>dubbed video mappings, from the online Google Docs spreadsheet."

    option_list = BaseCommand.option_list + (
        make_option('--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    help='Force reload of spreadsheet'),
    )

    def handle(self, *args, **options):

        # Get the CSV data, either from a recent cache_file
        #   or from the internet
        cache_dir = settings.MEDIA_ROOT
        cache_file = os.path.join(cache_dir, "dubbed_videos.csv")
        if not options["force"] and os.path.exists(cache_file) and datediff(datetime.datetime.now(), datetime.datetime.fromtimestamp(os.path.getctime(cache_file)), units="days") <= 14.0:
            # Use cached data to generate the video map
            csv_data = open(cache_file, "r").read()
            (video_map, _) = generate_dubbed_video_mappings(csv_data=csv_data)

        else:
            # Use cached data to generate the video map
            (video_map, csv_data) = generate_dubbed_video_mappings()

            try:
                ensure_dir(cache_dir)
                with open(cache_file, "w") as fp:
                    fp.write(csv_data)
            except Exception as e:
                logging.error("Failed to make a local cache of the CSV data: %s" % e)

        # Now we've built the map.  Save it.
        out_file = DUBBED_VIDEOS_MAPPING_FILEPATH
        ensure_dir(os.path.dirname(out_file))
        logging.info("Saving data to %s" % out_file)
        with open(out_file, "w") as fp:
            json.dump(video_map, fp)

        logging.info("Done.")
