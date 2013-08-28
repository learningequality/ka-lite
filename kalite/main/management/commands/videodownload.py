import time
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from main.models import VideoFile
from shared import caching
from utils.jobs import force_job
from utils.videos import download_video, DownloadCancelled, URLNotFound


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

    option_list = BaseCommand.option_list + (
        make_option('-c', '--cache',
            action='store_true',
            dest='auto_cache',
            default=False,
            help='Create cached files',
            metavar="AUTO_CACHE"),
    )

    def handle(self, *args, **options):

        caching_enabled = settings.CACHE_TIME != 0
        handled_video_ids = []  # stored to deal with caching

        while True: # loop until the method is aborted
            
            if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                self.stderr.write("Another download is still in progress; aborting.\n")
                break

            # Grab any video that hasn't been tried yet
            videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False)
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

                if isinstance(e, URLNotFound):
                    # This should never happen, but if it does, remove the VideoFile from the queue, and continue
                    # to the next video. Warning: this will leave the update page in a weird state, currently
                    # (and require a refresh of the update page in order to start showing progress again)
                    video.delete()
                    continue

                # On connection error, report the error, mark the video as not downloaded, and give up for now.
                self.stderr.write("Error in downloading %s: %s\n" % (video.youtube_id, e))
                video.download_in_progress = False
                video.percent_complete = 0
                video.save()
                break

            # Expire, but don't regenerate until the very end, for efficiency.
            if caching_enabled:
                caching.invalidate_all_pages_related_to_video(video_id=video.youtube_id)

        # After all is done, regenerate all pages
        #   since this is computationally intensive, only do it after we're sure
        #   nothing more will change (so that we don't regenerate something that is
        #   later invalidated by another video downloaded in the loop)
        if options["auto_cache"] and caching_enabled and handled_video_ids:
            caching.regenerate_all_pages_related_to_videos(video_ids=handled_video_ids)
