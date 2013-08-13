import sys
import time

import settings
from main.models import VideoFile
from updates.utils import UpdatesDynamicCommand
from utils import caching
from utils.jobs import force_job
from utils.topic_tools import get_video_by_youtube_id
from utils.videos import download_video, DownloadCancelled


def download_progress_callback(self, videofile):
    def inner_fn(percent):
        video = VideoFile.objects.get(pk=videofile.pk)

        if video.cancel_download == True:
            self.stdout.write("Download Cancelled!\n")
            
            # Update video info
            video.percent_complete = 0
            video.flagged_for_download = False
            video.download_in_progress = False
            video.save()

            # Progress info will be updated when this exception is caught.
            raise DownloadCancelled()

        elif (percent - video.percent_complete) >= 1 or percent == 100:

            # Update to output (saved in chronograph log, so be a bit more efficient
            if int(percent) % 5 == 0 or percent == 100:
                self.stdout.write("%d\n" % percent)

            # Update video data in the database
            if percent == 100:
                video.flagged_for_download = False
                video.download_in_progress = False
            video.percent_complete = percent
            video.save()

            # update progress data
            video_node = get_video_by_youtube_id(video.youtube_id)
            video_title = video_node["title"] if video_node else video.youtube_id
            self.update_stage(stage_name=video.youtube_id, stage_percent=percent/100., notes="Downloading '%s'" % video_title)

    return inner_fn
            

class Command(UpdatesDynamicCommand):
    help = "Download all videos marked to be downloaded"

    def handle(self, *args, **options):

        caching_enabled = settings.CACHE_TIME != 0

        handled_video_ids = []  # stored to deal with caching
        failed_video_ids = []  # stored to avoid requerying failures.
        try:
            while True: # loop until the method is aborted
            
                if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                    self.stderr.write("Another download is still in progress; aborting.\n")
                    break
            
                videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False).exclude(youtube_id__in=failed_video_ids)
                if videos.count() == 0:
                    self.stdout.write("Nothing to download; aborting.\n")
                    break

                # Grab the next video
                # Update the video logging
                video = videos[0]
                video.download_in_progress = True
                video.percent_complete = 0
                video.save()
            
                # Update the progress logging
                
                self.set_stages(num_stages=videos.count() + len(handled_video_ids) + 1)  # add one for the currently handed video
                if not self.started():
                    self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)
                    self.start(stage_name=video.youtube_id)

                # Initiate the download process
                try:
                    download_video(video.youtube_id, callback=download_progress_callback(self, video))
                    handled_video_ids.append(video.youtube_id)
                    self.stdout.write("Download is complete!\n")
                except Exception as e:
                    # On error, report the error, mark the video as not downloaded,
                    #   and allow the loop to try other videos.
                    self.stderr.write("Error in downloading %s: %s\n" % (video.youtube_id, e))
                    video.download_in_progress = False
                    video.save()
                    # Rather than getting stuck on one video, continue to the next video.
                    failed_video_ids.append(video.youtube_id)
                    continue

                # Expire, but don't regenerate until the very end, for efficiency.
                if caching_enabled:
                    caching.invalidate_cached_topic_hierarchies(video_id=video.youtube_id)

        except Exception as e:
            sys.stderr.write("Error: %s\n" % e)
            self.cancel()

        # Update
        self.complete()

        # Regenerate all pages, efficiently

        if caching_enabled:
            caching.regenerate_cached_topic_hierarchies(handled_video_ids)
