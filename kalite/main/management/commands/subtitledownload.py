import json
import sys
import os
import requests
import time

from django.core.management.base import BaseCommand, CommandError

from config.models import Settings
from main.models import VideoFile
from utils.jobs import force_job
from utils.subtitles.download_subtitles import download_subtitles, NoSubs

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/../../"
sys.path = [PROJECT_PATH] + sys.path
import settings

class Command(BaseCommand):
    help = "Download all subtitles marked to be downloaded"

    def handle(self, *args, **options):
        language = Settings.get("subtitle_language")
        request_url = "http://%s/static/data/subtitles/srts_by_language/%s.json" % (settings.CENTRAL_SERVER_HOST, language)
        try:
            # TODO(dylan): better error handling here
            r = requests.get(request_url)
            available_srts = set((r.json)["srt_files"])
        except:
            self.stdout.write("No subtitles available on central server for language code %s; aborting.\n" % language)
            return

        while True: # loop until the method is aborted
            
            if VideoFile.objects.filter(subtitle_download_in_progress=True).count() > 4:
                self.stderr.write("Maximum downloads are in progress; aborting.\n")
                return
            
            videos = VideoFile.objects.filter(flagged_for_subtitle_download=True, subtitle_download_in_progress=False)
            if videos.count() == 0:
                self.stdout.write("Nothing to download; aborting.\n")
                return

            video = videos[0]
            
            video.subtitle_download_in_progress = True
            video.save()
            
            self.stdout.write("Downloading subtitles for video '%s'... " % video.youtube_id)
            self.stdout.flush()

            try:
                if video.youtube_id in available_srts:
                    download_subtitles(video.youtube_id, language)
                    self.stdout.write("Download is complete!\n")
                    video.subtitles_downloaded = True
                    video.subtitle_download_in_progress = False
                    video.flagged_for_subtitle_download = False
                    video.save()
                else: 
                    raise NoSubs
            except NoSubs as e:
                video.flagged_for_subtitle_download = False
                video.subtitle_download_in_progress = False
                video.subtitles_downloaded = True
                self.stdout.write("\n");
                video.save()
                self.stderr.write("No subtitles available\n")
            except Exception as e:
                self.stderr.write("Error in downloading subtitles: %s\n" % e)
                video.subtitle_download_in_progress = False
                video.flagged_for_subtitle_download = False
                video.save()
                force_job("subtitledownload", "Download Subtitles")
                return
