import time

from django.core.management.base import BaseCommand, CommandError

import settings
from main.models import VideoFile
from utils import caching
from utils.jobs import force_job
from utils.videos import download_video, DownloadCancelled


def download_progress_callback(self, videofile):
    def inner_fn(percent):
        video = VideoFile.objects.get(pk=videofile.pk)
        if video.cancel_download == True:
            video.percent_complete = 0
            video.flagged_for_download = False
            video.download_in_progress = False
            video.save()
            self.stderr.write("Download Cancelled!\n")
            raise DownloadCancelled()
        if (percent - video.percent_complete) >= 5 or percent == 100:
            if percent == 100:
                video.flagged_for_download = False
                video.download_in_progress = False
            video.percent_complete = percent
            self.stdout.write("%d\n" % percent)
            video.save()
    return inner_fn
            

class Command(BaseCommand):
    help = "Download all videos marked to be downloaded"

    def handle(self, *args, **options):
        
        handled_video_ids = []
        
        while True: # loop until the method is aborted
            
            if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                self.stderr.write("Another download is still in progress; aborting.\n")
                break
            
            videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False)
            if videos.count() == 0:
                self.stdout.write("Nothing to download; aborting.\n")
                break

            video = videos[0]
            
            if video.cancel_download == True:
                video.download_in_progress = False
                video.save()
                self.stdout.write("Download cancelled; aborting.\n")
                break
            
            video.download_in_progress = True
            video.percent_complete = 0
            video.save()
            
            self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)
            try:
                download_video(video.youtube_id, callback=download_progress_callback(self, video))
                self.stdout.write("Download is complete!\n")
            except Exception as e:
                self.stderr.write("Error in downloading: %s\n" % e)
                video.download_in_progress = False
                video.save()
                force_job("videodownload", "Download Videos")  # infinite recursive call? :(
                break
            
            handled_video_ids.append(video.youtube_id)
            
            # Expire, but don't regenerate until the very end, for efficiency.
            if hasattr(settings, "CACHES"):
                caching.invalidate_cached_topic_hierarchies(video_id=video.youtube_id)
    
        # Regenerate all pages, efficiently
        if hasattr(settings, "CACHES"):
            caching.regenerate_cached_topic_hierarchies(handled_video_ids)
        