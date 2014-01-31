import sys
import time
from functools import partial
from optparse import make_option

from django.utils.translation import ugettext as _

import settings
from .classes import UpdatesDynamicCommand
from i18n.management.commands.scrape_videos import scrape_video
from shared import caching, i18n
from shared.topic_tools import get_video_by_youtube_id
from shared.videos import download_video, DownloadCancelled, URLNotFound
from updates.models import VideoFile
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
        video_changed = (not self.video) or self.video.pk != videofile.pk
        video_done = self.video and percent == 100

        if self.video and (percent - self.video.percent_complete) < 1 and not video_done and not video_changed:
            return

        self.video = VideoFile.objects.get(pk=videofile.pk)

        try:
            if self.video.cancel_download:
                raise DownloadCancelled()

            elif (percent - self.video.percent_complete) >= 1 or video_done or video_changed:
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
                video_title = _(video_node["title"]) if video_node else self.video.youtube_id

                # Calling update_stage, instead of next_stage when stage changes, will auto-call next_stage appropriately.
                self.update_stage(stage_name=self.video.youtube_id, stage_percent=percent/100., notes=_("Downloading '%s'") % video_title)

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

        handled_youtube_ids = []  # stored to deal with caching
        failed_youtube_ids = []  # stored to avoid requerying failures.

        set_process_priority.lowest(logging=settings.LOG)

        try:
            while True: # loop until the method is aborted
                # Grab any video that hasn't been tried yet
                videos = VideoFile.objects \
                    .filter(flagged_for_download=True, download_in_progress=False) \
                    .exclude(youtube_id__in=failed_youtube_ids)
                video_count = videos.count()
                if video_count == 0:
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
                self.set_stages(num_stages=video_count + len(handled_youtube_ids) + len(failed_youtube_ids) + int(options["auto_cache"]))
                if not self.started():
                    self.start(stage_name=video.youtube_id)

                # Initiate the download process
                try:
                    if video.language == "en":  # could even try download_video, and fall back to scrape_video, for en...
                        download_video(video.youtube_id, callback=partial(self.download_progress_callback, video))
                    else:
                    logging.info(_("Retrieving youtube video %s") % video.youtube_id)
                        self.download_progress_callback(video, 0)
                        scrape_video(video.youtube_id, suppress_output=True)
                        self.download_progress_callback(video, 100)
                    handled_youtube_ids.append(video.youtube_id)
                    self.stdout.write("Download is complete!\n")
                except Exception as e:
                    # On error, report the error, mark the video as not downloaded,
                    #   and allow the loop to try other videos.
                    msg = "Error in downloading %s: %s" % (video.youtube_id, e)
                    self.stderr.write("%s\n" % msg)
                    video.download_in_progress = False
                    video.flagged_for_download = not isinstance(e, URLNotFound)  # URLNotFound means, we won't try again
                    video.save()
                    # Rather than getting stuck on one video, continue to the next video.
                    failed_youtube_ids.append(video.youtube_id)
                    self.update_stage(stage_status="error", notes="%s; continuing to next video." % msg)
                    continue

            # This can take a long time, without any further update, so ... best to avoid.
            if options["auto_cache"] and caching.caching_is_enabled() and handled_youtube_ids:
                self.update_stage(stage_name=self.video.youtube_id, stage_percent=0, notes=_("Generating all pages related to videos."))
                caching.regenerate_all_pages_related_to_videos(video_ids=list(set([i18n.get_video_id(yid) or yid for yid in handled_youtube_ids])))

            # Update
            self.complete(notes=_("Downloaded %(num_handled_videos)s of %(num_total_videos)s videos successfully.") % {
                "num_handled_videos": len(handled_youtube_ids),
                "num_total_videos": len(handled_youtube_ids) + len(failed_youtube_ids),
            })

        except Exception as e:
            self.cancel(stage_status="error", notes=_("Error: %s") % e)
            raise
