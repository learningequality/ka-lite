"""
This is a command-line tool to execute functions helpful to testing.
"""
import glob
import json
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from settings import LOG as logging
from shared.videos import REMOTE_VIDEO_SIZE_FILEPATH
from utils.general import ensure_dir, softload_json


class Command(BaseCommand):
    help = "KA Lite test help"
    option_list = BaseCommand.option_list + (
    make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),)

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("Run this command on the distributed server only.")

        video_sizes= softload_json(REMOTE_VIDEO_SIZE_FILEPATH, logger=logging.debug)

        all_video_filepaths = glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4"))
        logging.info("Querying sizes for %d video(s)." % len(all_video_filepaths))

        for video_filepath in all_video_filepaths:
            youtube_id = os.path.splitext(os.path.basename(video_filepath))[0]
            # Set to max, so that local compressed videos will not affect things.
            video_sizes[youtube_id] = max(video_sizes.get(youtube_id, 0), os.path.getsize(video_filepath))

        logging.info("Saving results to disk.")
        ensure_dir(os.path.dirname(REMOTE_VIDEO_SIZE_FILEPATH))
        with open(REMOTE_VIDEO_SIZE_FILEPATH, "w") as fp:
            json.dump(video_sizes, fp)
