"""
CENTRAL SERVER ONLY

This command is used to cache srt files on the central server. It uses
the mapping generate by generate_subtitle_map to make requests of the
Amara API.

NOTE: srt map deals with amara, so uses ietf codes (e.g. en-us). However,
  when directories are created, we use django-style directories (e.g. en_US)
"""
import glob
import os
import shutil
import stat
import subprocess
import tempfile
import youtube_dl
from optparse import make_option
from youtube_dl.utils import DownloadError, ExtractorError

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

import settings
from i18n import get_dubbed_video_map, lcode_to_ietf
from main.topic_tools import get_topic_videos, get_node_cache
from settings import LOG as logging
from utils.general import ensure_dir
from utils.videos import get_outside_video_urls


class Command(BaseCommand):
    help = "Update the mapping of subtitles available by language for each video. Location: static/data/subtitles/srts_download_status.json"

    option_list = BaseCommand.option_list + (
        make_option('-l', '--language',
                    action='store',
                    dest='lang_code',
                    default=None,
                    metavar="LANG_CODE",
                    help="Specify a particular language code (e.g. en-us) to download subtitles for. Can be used with -f to update previously downloaded subtitles."),
        make_option('-i', '--video-ids',
                    action='store',
                    dest='video_ids',
                    default=None,
                    metavar="VIDEO_IDS",
                    help="Download the specified videos only"),
        make_option('-t', '--topic-id',
                    action='store',
                    dest='topic_id',
                    default=None,
                    metavar="TOPIC_ID",
                    help="Download all videos from a topic"),
        make_option('-o', '--format',
                    action='store_true',
                    dest='format',
                    default="mp4",
                    metavar="FORMAT",
                    help="Specify the format to convert the video to"),
        make_option('-f', '--force',
                    action='store_true',
                    dest='force',
                    default=False,
                    metavar="FORCE",
                    help="Force re-downloading of previously downloaded subtitles to refresh the repo. Can be used with -l. Default behavior is to not re-download subtitles we already have."),
    )


    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("This must only be run on the distributed server.")

        if not options["lang_code"]:
            raise CommandError("You must specify a language code.")

        #
        ensure_dir(settings.CONTENT_ROOT)

        # Get list of videos
        lang_code = lcode_to_ietf(options["lang_code"])
        video_map = get_dubbed_video_map(lang_code) or {}
        video_ids = options["video_ids"].split(",") if options["video_ids"] else None
        video_ids = video_ids or ([vid["id"] for vid in get_topic_videos(topic_id=options["topic_id"])] if options["topic_id"] else None)
        video_ids = video_ids or video_map.keys()

        # Download the videos
        for video_id in video_ids:
            if video_id in video_map:
                youtube_id = video_map[video_id]

            elif video_id in video_map.values():
                # Perhaps they sent in a youtube ID?  We can handle that!
                youtube_id = video_id
            else:
                logging.error("No mapping for video_id=%s; skipping" % video_id)
                continue

            try:
                scrape_video(youtube_id=youtube_id, format=options["format"], force=options["force"])
                #scrape_thumbnail(youtube_id=youtube_id)
                logging.info("Access video %s at %s" % (youtube_id, get_node_cache("Video")[video_id][0]["path"]))
            except Exception as e:
                logging.error("Failed to download video %s: %s" % (youtube_id, e))

        logging.info("Process complete.")

def scrape_video(youtube_id, format="mp4", force=False, quiet=False, callback=None):
    """
    Assumes it's in the path; if not, we try to download & install.

    Callback will be called back with a dictionary as the first arg with a bunch of
    youtube-dl info in it, as specified in the youtube-dl docs.
    """
    video_filename =  "%(id)s.%(ext)s" % { 'id': youtube_id, 'ext': format }
    video_file_download_path = os.path.join(settings.CONTENT_ROOT, video_filename)
    if os.path.exists(video_file_download_path) and not force:
        return

    yt_dl = youtube_dl.YoutubeDL({'outtmpl': video_file_download_path, "quiet": quiet})
    yt_dl.add_default_info_extractors()
    if callback:
        yt_dl.add_progress_hook(callback)
    yt_dl.extract_info('www.youtube.com/watch?v=%s' % youtube_id, download=True)

"""
def scrape_thumbnail(youtube_id, format="png", force=False):
    _, thumbnail_url = get_outside_video_urls(youtube_id)
    try:
        resp = requests.get(thumbnail_url)
        with open(
    except Exception as e:
        logging.error("Failed to download %s: %s" % (thumbnail_url, e))
"""
