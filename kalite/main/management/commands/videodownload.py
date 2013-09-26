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


    def handle(self, *args, **options):

        caching_enabled = settings.CACHE_TIME != 0
        handled_video_ids = []  # stored to deal with caching
        failed_video_ids = []  # stored to avoid requerying failures.
        try:
            while True: # loop until the method is aborted
                if VideoFile.objects.filter(download_in_progress=True).count() > 0:
                    self.stderr.write("Another download is still in progress; aborting.\n")
                    break
            
                # Grab any video that hasn't been tried yet
                videos = VideoFile.objects.filter(flagged_for_download=True, download_in_progress=False).exclude(youtube_id__in=failed_video_ids)
                if videos.count() == 0:
                    self.stdout.write("Nothing to download; aborting.\n")
                    break

                # Grab a video as OURS to handle, set fields to indicate to others that we're on it!
                # Update the video logging
                video = videos[0]
                video.download_in_progress = True
                video.percent_complete = 0
                video.save()
                self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)

                # Update the progress logging
                self.set_stages(num_stages=videos.count() + len(handled_video_ids) + 1)  # add one for the currently handed video
                if not self.started():
                    self.stdout.write("Downloading video '%s'...\n" % video.youtube_id)
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

        except Exception as e:
            sys.stderr.write("Error: %s\n" % e)
            self.cancel()

        # This can take a long time, without any further update, so ... best to avoid.
        if options["auto_cache"] and caching_enabled and handled_video_ids:
            caching.regenerate_all_pages_related_to_videos(video_ids=handled_video_ids)

        # Update
        self.complete()
