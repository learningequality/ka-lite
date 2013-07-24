import time

from django.core.management.base import BaseCommand, CommandError

import settings
from main.models import VideoFile
from updates.models import UpdateProgressLog
from utils import caching
from utils.jobs import force_job
from utils.videos import download_video, DownloadCancelled


def download_progress_callback(self, videofile, progress_log=None):
    def inner_fn(percent):
        video = VideoFile.objects.get(pk=videofile.pk)

        if video.cancel_download == True:
            self.stderr.write("Download Cancelled!\n")
            
            # Update video info
            video.percent_complete = 0
            video.flagged_for_download = False
            video.download_in_progress = False
            video.save()
            
            # Update progress info
            if progress_log:
                progress_log.cancel_current_stage()

            raise DownloadCancelled()

        elif (percent - video.percent_complete) >= 1 or percent == 100:
            self.stdout.write("%d\n" % percent)

            # Update video data
            if percent == 100:
                video.flagged_for_download = False
                video.download_in_progress = False
            video.percent_complete = percent
            video.save()

            # update progress data
            if progress_log:
                progress_log.update_stage(stage_name=video.youtube_id, stage_percent=percent/100.)

    return inner_fn
            

class Command(BaseCommand):
    help = "Download all videos marked to be downloaded"

    def handle(self, *args, **options):
        
        handled_video_ids = []
        progress_log = None
        try:
            while True: # loop until the method is aborted
            
                if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                    self.stderr.write("Another download is still in progress; aborting.\n")
                    break
            
                videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False)
                if videos.count() == 0:
                    self.stdout.write("Nothing to download; aborting.\n")
                    break

                # Grab the next video
                video = videos[0]
                self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)

                # Update the video logging
                video.download_in_progress = True
                video.percent_complete = 0
                video.save()
            
                # Update the progress logging
                if not progress_log:
                    progress_log = UpdateProgressLog.get_active_log(process_name="videodownload")
                    progress_log.stage_name = video.youtube_id
                    progress_log.save()
                progress_log.update_total_stages(videos.count() + len(handled_video_ids) + 1)  # add one for the currently handed video
            
                # Initiate the download process
                try:
                    download_video(video.youtube_id, callback=download_progress_callback(self, video, progress_log=progress_log))
                    self.stdout.write("Download is complete!\n")
                except Exception as e:
                    self.stderr.write("Error in downloading: %s\n" % str(e))
                    video.download_in_progress = False
                    video.save()
                    force_job("videodownload", "Download Videos")  # infinite recursive call? :(
                    break
            
                handled_video_ids.append(video.youtube_id)
            
                # Expire, but don't regenerate until the very end, for efficiency.
                if hasattr(settings, "CACHES"):
                    caching.invalidate_cached_topic_hierarchies(video_id=video.youtube_id)
        except Exception as e:
            sys.stderr.write("Error: %s\n" % e)
            progress_log.cancel_progress()
            progress_log = None  # no further updates

            # Update
        if progress_log:
            progress_log.mark_as_completed()

        # Regenerate all pages, efficiently
        if hasattr(settings, "CACHES"):
            caching.regenerate_cached_topic_hierarchies(handled_video_ids)
        