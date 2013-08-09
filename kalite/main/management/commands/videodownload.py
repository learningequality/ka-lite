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

        caching_enabled = settings.CACHE_TIME != 0
        handled_video_ids = []  # stored to deal with caching
        failed_video_ids = []  # stored to avoid requerying failures.

        while True: # loop until the method is aborted
            
            if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                self.stderr.write("Another download is still in progress; aborting.\n")
                break

            # Grab any video that hasn't been tried yet
            videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False).exclude(youtube_id__in=failed_video_ids)
            if videos.count() == 0:
                self.stdout.write("Nothing to download; aborting.\n")
                break

            video = videos[0]

            # User intervention
            if video.cancel_download == True:
                video.download_in_progress = False
                video.save()
                self.stdout.write("Download cancelled; aborting.\n")
                break

            # Grab a video as OURS to handle, set fields to indicate to others that we're on it!
            video.download_in_progress = True
            video.percent_complete = 0
            video.save()
            
            self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)
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

        # After all is done, regenerate all pages
        #   since this is computationally intensive, only do it after we're sure
        #   nothing more will change (so that we don't regenerate something that is
        #   later invalidated by another video downloaded in the loop)
        if caching_enabled:
            caching.regenerate_cached_topic_hierarchies(handled_video_ids)
