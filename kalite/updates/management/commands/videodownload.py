"""
"""
import os
import youtube_dl
import time
from functools import partial
from optparse import make_option

from django.conf import settings
logging = settings.LOG
from django.utils.translation import ugettext as _

from kalite.updates.management.utils import UpdatesDynamicCommand
from ...videos import download_video
from ...download_track import VideoQueue
from fle_utils import set_process_priority
from fle_utils.videos import DownloadCancelled, URLNotFound
from fle_utils.chronograph.management.croncommand import CronCommand
from kalite.topic_tools.content_models import get_video_from_youtube_id, annotate_content_models_by_youtube_id

def scrape_video(youtube_id, format="mp4", force=False, quiet=False, callback=None):
    """
    Assumes it's in the path; if not, we try to download & install.

    Callback will be called back with a dictionary as the first arg with a bunch of
    youtube-dl info in it, as specified in the youtube-dl docs.
    """
    video_filename =  "%(id)s.%(ext)s" % { 'id': youtube_id, 'ext': format }
    video_file_download_path = os.path.join(settings.CONTENT_ROOT, video_filename)
    if os.path.exists(video_file_download_path) and not force:
        return

    yt_dl = youtube_dl.YoutubeDL({'outtmpl': video_file_download_path, "quiet": quiet})
    yt_dl.add_default_info_extractors()
    if callback:
        yt_dl.add_progress_hook(callback)
    yt_dl.extract_info('www.youtube.com/watch?v=%s' % youtube_id, download=True)


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

        except DownloadCancelled as de:
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

        set_process_priority.lowest(logging=settings.LOG)

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

                        try:
                            # Download via urllib
                            download_video(video.get("youtube_id"), callback=progress_callback)

                        except URLNotFound:
                            # Video was not found on amazon cloud service,
                            #   either due to a KA mistake, or due to the fact
                            #   that it's a dubbed video.
                            #
                            # We can use youtube-dl to get that video!!
                            logging.debug(_("Retrieving youtube video %(youtube_id)s via youtube-dl") % {"youtube_id": video.get("youtube_id")})

                            def youtube_dl_cb(stats, progress_callback, *args, **kwargs):
                                if stats['status'] == "finished":
                                    percent = 100.
                                elif stats['status'] == "downloading":
                                    percent = 100. * stats['downloaded_bytes'] / stats['total_bytes']
                                else:
                                    percent = 0.
                                progress_callback(percent=percent)
                            scrape_video(video.get("youtube_id"), quiet=not settings.DEBUG, callback=partial(youtube_dl_cb, progress_callback=progress_callback))

                        except IOError as e:
                            logging.exception(e)
                            failed_youtube_ids.append(video.get("youtube_id"))
                            video_queue.remove_file(video.get("youtube_id"))
                            time.sleep(10)
                            continue

                    # If we got here, we downloaded ... somehow :)
                    handled_youtube_ids.append(video.get("youtube_id"))
                    video_queue.remove_file(video.get("youtube_id"))
                    self.stdout.write(_("Download is complete!") + "\n")

                    annotate_content_models_by_youtube_id(youtube_ids=[video.get("youtube_id")], language=video.get("language"))

                except DownloadCancelled:
                    # Cancellation event
                    video_queue.clear()
                    failed_youtube_ids.append(video.get("youtube_id"))

                except Exception as e:
                    # On error, report the error, mark the video as not downloaded,
                    #   and allow the loop to try other videos.
                    msg = _("Error in downloading %(youtube_id)s: %(error_msg)s") % {"youtube_id": video.get("youtube_id"), "error_msg": unicode(e)}
                    self.stderr.write("%s\n" % msg)

                    # Rather than getting stuck on one video, continue to the next video.
                    self.update_stage(stage_status="error", notes=_("%(error_msg)s; continuing to next video.") % {"error_msg": msg})
                    failed_youtube_ids.append(video.get("youtube_id"))
                    video_queue.remove_file(video.get("youtube_id"))
                    continue

            # Update
            self.complete(notes=_("Downloaded %(num_handled_videos)s of %(num_total_videos)s videos successfully.") % {
                "num_handled_videos": len(handled_youtube_ids),
                "num_total_videos": len(handled_youtube_ids) + len(failed_youtube_ids),
            })

        except Exception as e:
            self.cancel(stage_status="error", notes=_("Error: %(error_msg)s") % {"error_msg": e})
            raise
