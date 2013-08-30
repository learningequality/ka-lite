import json
import sys
import os
import requests
import time

from django.core.management.base import BaseCommand, CommandError

import settings
from config.models import Settings
from main.models import VideoFile
from utils.jobs import force_job
from utils.subtitles.download_subtitles import download_subtitles, NoSubs


class Command(BaseCommand):
    help = "Download all subtitles marked to be downloaded"

    def handle(self, *args, **options):
        language = Settings.get("subtitle_language")
        failed_video_ids = []  # stored to avoid requerying failures.

        while True: # loop until the method is aborted

            if VideoFile.objects.filter(subtitle_download_in_progress=True).count() > 4:
                self.stderr.write("Maximum downloads are in progress; aborting.\n")
                return

            videos = VideoFile.objects.filter(flagged_for_subtitle_download=True, subtitle_download_in_progress=False).exclude(youtube_id__in=failed_video_ids)
            if videos.count() == 0:
                self.stdout.write("Nothing to download; aborting.\n")
                break

            # Grab a video and mark it as downloading
            video = videos[0]
            video.subtitle_download_in_progress = True
            video.save()

            self.stdout.write("Downloading subtitles for video '%s'... " % video.youtube_id)
            self.stdout.flush()

            try:
                download_subtitles(video.youtube_id, language)
                video.subtitles_downloaded = True
                video.subtitle_download_in_progress = False
                video.flagged_for_subtitle_download = False
                video.save()
                self.stdout.write("Download is complete!\n")

            except NoSubs as e:
                # Not all videos have subtitles, so this error
                #   is in most ways a success.
                video.flagged_for_subtitle_download = False
                video.subtitle_download_in_progress = False
                video.subtitles_downloaded = True
                self.stdout.write("\n");
                video.save()
                self.stdout.write("No subtitles available\n")

            except Exception as e:
                self.stderr.write("Error in downloading subtitles: %s\n" % e)
                video.subtitle_download_in_progress = False
                video.flagged_for_subtitle_download = False
                video.save()
                # Skip this video and move on.
                failed_video_ids.append(video.youtube_id)
                continue
