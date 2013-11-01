import sys
import time
from functools import partial
from optparse import make_option

import settings
from main.models import VideoFile
from shared import caching
from shared.jobs import force_job
from shared.topic_tools import get_video_by_youtube_id
from shared.videos import download_video, DownloadCancelled, URLNotFound
from updates.management.commands.classes import UpdatesDynamicCommand
from utils import set_process_priority


class Command(UpdatesDynamicCommand):
    help = "Download all videos marked to be downloaded"

    option_list = UpdatesDynamicCommand.option_list + (
        make_option('-c', '--cache',
            action='store_true',
            dest='auto_cache',
            default=False,
            help='Create cached files',
            metavar="AUTO_CACHE"),
    )


    def download_progress_callback(self, videofile, percent):
        if self.video and (percent - self.video.percent_complete) < 1 and percent != 100:
            return

        self.video = VideoFile.objects.get(pk=videofile.pk)

        try:
            if self.video.cancel_download:
                raise DownloadCancelled()

            elif (percent - self.video.percent_complete) >= 1 or percent == 100:
                # Update to output (saved in chronograph log, so be a bit more efficient
                if int(percent) % 5 == 0 or percent == 100:
                    self.stdout.write("%d\n" % percent)

                # Update video data in the database
                if percent == 100:
                    self.video.flagged_for_download = False
                    self.video.download_in_progress = False
                self.video.percent_complete = percent
                self.video.save()

                # update progress data
                video_node = get_video_by_youtube_id(self.video.youtube_id)
                video_title = video_node["title"] if video_node else self.video.youtube_id
                self.update_stage(stage_name=self.video.youtube_id, stage_percent=percent/100., notes="Downloading '%s'" % video_title)

                if percent == 100:
                    self.video = None

        except DownloadCancelled as de:
            if self.video:
                self.stdout.write("Download Cancelled!\n")
            
                # Update video info
                self.video.percent_complete = 0
                self.video.flagged_for_download = False
                self.video.download_in_progress = False
                self.video.save()
                self.video = None

            # Progress info will be updated when this exception is caught.
            raise


    def handle(self, *args, **options):
        self.video = None

        caching_enabled = settings.CACHE_TIME != 0
        handled_video_ids = []  # stored to deal with caching
        failed_video_ids = []  # stored to avoid requerying failures.

        set_process_priority.lowest(logging=settings.LOG)
        
        try:
            while True: # loop until the method is aborted
                # Grab any video that hasn't been tried yet
                videos = list(VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False).exclude(youtube_id__in=failed_video_ids))
                if len(videos) == 0:
                    self.stdout.write("Nothing to download; exiting.\n")
                    break

                # Grab a video as OURS to handle, set fields to indicate to others that we're on it!
                # Update the video logging
                video = videos[0]
                video.download_in_progress = True
                video.percent_complete = 0
                video.save()
                self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)

                # Update the progress logging
                self.set_stages(num_stages=len(videos) + len(handled_video_ids) + len(failed_video_ids) + int(options["auto_cache"]))
                if not self.started():
                    self.start(stage_name=video.youtube_id)

                # Initiate the download process
                try:
                    download_video(video.youtube_id, callback=partial(self.download_progress_callback, video))
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
                    caching.invalidate_all_pages_related_to_video(video_id=video.youtube_id)

            # This can take a long time, without any further update, so ... best to avoid.
            if options["auto_cache"] and caching_enabled and handled_video_ids:
                self.update_stage(stage_name=self.video.youtube_id, stage_percent=0, notes="Generating all pages related to videos.")
                caching.regenerate_all_pages_related_to_videos(video_ids=handled_video_ids)

            # Update
            self.complete()

        except Exception as e:
            sys.stderr.write("Error: %s\n" % e)
            self.cancel()
