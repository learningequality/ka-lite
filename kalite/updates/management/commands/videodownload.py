"""
"""
import os
import socket
import logging

from functools import partial
from optparse import make_option

from django.conf import settings
from requests.exceptions import HTTPError, ConnectionError

from django.utils.translation import ugettext as _

from kalite.updates.management.utils import UpdatesDynamicCommand
from ...videos import download_video
from ...download_track import VideoQueue
from fle_utils import set_process_priority
from fle_utils.chronograph.management.croncommand import CronCommand
from kalite.topic_tools.content_models import get_video_from_youtube_id, annotate_content_models_by_youtube_id
import time
from kalite.updates.settings import DOWNLOAD_MAX_RETRIES


logger = logging.getLogger(__name__)


class DownloadCancelled(Exception):

    def __str__(self):
        return "Download has been cancelled"


class Command(UpdatesDynamicCommand, CronCommand):
    help = _("Download all videos marked to be downloaded")

    unique_option_list = (
        make_option('-c', '--cache',
            action='store_true',
            dest='auto_cache',
            default=False,
            help=_('Create cached files'),
            metavar="AUTO_CACHE"),
    )

    option_list = UpdatesDynamicCommand.option_list + CronCommand.unique_option_list + unique_option_list


    def download_progress_callback(self, videofile, percent):

        video_changed = (not self.video) or self.video.get("youtube_id") != videofile.get("youtube_id")
        video_done = self.video and percent == 100
        video_error = self.video and not video_changed and (percent - self.video.get("percent_complete", 0) > 50)

        if self.video and (percent - self.video.get("percent_complete", 0)) < 1 and not video_done and not video_changed and not video_error:
            return

        self.video = videofile

        video_queue = VideoQueue()

        try:
            if not video_queue.count():
                raise DownloadCancelled()

            else:
                if video_error:
                    self.video["percent_complete"] = 0
                    return

                elif (percent - self.video.get("percent_complete", 0)) >= 1 or video_done or video_changed:
                    # Update to output (saved in chronograph log, so be a bit more efficient
                    if int(percent) % 5 == 0 or percent == 100:
                        self.stdout.write("%d\n" % percent)

                    self.video["percent_complete"] = percent

                # update progress data
                video_node = get_video_from_youtube_id(self.video.get("youtube_id"))
                video_title = (video_node and video_node.get("title")) or self.video.get("title")

                # Calling update_stage, instead of next_stage when stage changes, will auto-call next_stage appropriately.
                self.update_stage(stage_name=self.video.get("youtube_id"), stage_percent=percent/100., notes=_("Downloading '%(video_title)s'") % {"video_title": _(video_title)})

                if percent == 100:
                    self.video = {}

        except DownloadCancelled:
            if self.video:
                self.stdout.write(_("Download cancelled!") + "\n")

                self.video = {}

            # Progress info will be updated when this exception is caught.
            raise


    def handle(self, *args, **options):
        self.setup(options)
        self.video = {}

        handled_youtube_ids = []  # stored to deal with caching
        failed_youtube_ids = []  # stored to avoid requerying failures.

        set_process_priority.lowest(logging=logger)

        try:
            while True:
                # loop until the method is aborted
                # Grab any video that hasn't been tried yet

                video_queue = VideoQueue()

                video_count = video_queue.count()
                if video_count == 0:
                    self.stdout.write(_("Nothing to download; exiting.") + "\n")
                    break

                # Grab a video as OURS to handle, set fields to indicate to others that we're on it!
                # Update the video logging
                video = video_queue.next()

                video["download_in_progress"] = True
                video["percent_complete"] = 0
                self.stdout.write((_("Downloading video '%(youtube_id)s'...") + "\n") % {"youtube_id": video.get("youtube_id")})

                # Update the progress logging
                self.set_stages(num_stages=video_count + len(handled_youtube_ids) + len(failed_youtube_ids) + int(options["auto_cache"]))
                if not self.started():
                    self.start(stage_name=video.get("youtube_id"))

                # Initiate the download process
                try:

                    progress_callback = partial(self.download_progress_callback, video)

                    # Don't try to download a file that already exists in the content dir - just say it was successful
                    # and call it a day!
                    if not os.path.exists(os.path.join(settings.CONTENT_ROOT, "{id}.mp4".format(id=video.get("youtube_id")))):

                        retries = 0
                        while True:
                            try:
                                download_video(video.get("youtube_id"), callback=progress_callback)
                                break
                            except (socket.timeout, ConnectionError):
                                retries += 1
                                msg = _(
                                    "Pausing download for '{title}', failed {failcnt} times, sleeping for 30s, retry number {retries}"
                                ).format(
                                    title=video.get("title"),
                                    failcnt=DOWNLOAD_MAX_RETRIES,
                                    retries=retries,
                                )
                                try:
                                    self.update_stage(
                                        stage_name=video.get("youtube_id"),
                                        stage_percent=0.,
                                        notes=msg
                                    )
                                except AssertionError:
                                    # Raised by update_stage when the video
                                    # download job has ended
                                    raise DownloadCancelled()
                                logger.info(msg)
                                time.sleep(30)
                                continue

                    # If we got here, we downloaded ... somehow :)
                    handled_youtube_ids.append(video.get("youtube_id"))
                    
                    # Remove from item from the queue
                    video_queue.remove_file(video.get("youtube_id"))
                    self.stdout.write(_("Download is complete!") + "\n")

                    annotate_content_models_by_youtube_id(youtube_ids=[video.get("youtube_id")], language=video.get("language"))

                except DownloadCancelled:
                    video_queue.clear()
                    failed_youtube_ids.append(video.get("youtube_id"))
                    break

                except (HTTPError, Exception) as e:
                    # Rather than getting stuck on one video,
                    # completely remove this item from the queue
                    failed_youtube_ids.append(video.get("youtube_id"))
                    video_queue.remove_file(video.get("youtube_id"))
                    logger.exception(e)

                    if getattr(e, "response", None):
                        reason = _(
                            "Got non-OK HTTP status: {status}"
                        ).format(
                            status=e.response.status_code
                        )
                    else:
                        reason = _(
                            "Unhandled request exception: "
                            "{exception}"
                        ).format(
                            exception=str(e),
                        )
                    msg = _(
                        "Skipping '{title}', reason: {reason}"
                    ).format(
                        title=video.get('title'),
                        reason=reason,
                    )
                    # Inform the user of this problem
                    self.update_stage(
                        stage_name=video.get("youtube_id"),
                        stage_percent=0.,
                        notes=msg
                    )
                    logger.info(msg)
                    continue

            # Update
            self.complete(notes=_("Downloaded %(num_handled_videos)s of %(num_total_videos)s videos successfully.") % {
                "num_handled_videos": len(handled_youtube_ids),
                "num_total_videos": len(handled_youtube_ids) + len(failed_youtube_ids),
            })

        except Exception as e:
            logger.exception(e)
            self.cancel(stage_status="error", notes=_("Error: %(error_msg)s") % {"error_msg": e})
            raise
