"""
"""
import os
import youtube_dl
import time
from functools import partial
from optparse import make_option
from youtube_dl.utils import DownloadError

from django.conf import settings; logging = settings.LOG
from django.utils.translation import ugettext as _

from .classes import UpdatesDynamicCommand
from ... import download_video, DownloadCancelled, URLNotFound
from ...models import VideoFile
from fle_utils import set_process_priority
from fle_utils.chronograph.management.croncommand import CronCommand
from kalite import caching, i18n, topic_tools

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


def get_video_node_by_youtube_id(youtube_id):
    """Returns the video node corresponding to the video_id of the given youtube_id, or None"""
    video_id = i18n.get_video_id(youtube_id=youtube_id)
    return topic_tools.get_node_cache("Content").get(video_id, [None])


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

        video_changed = (not self.video) or self.video.pk != videofile.pk
        video_done = self.video and percent == 100
        video_error = self.video and not video_changed and (percent - self.video.percent_complete > 50)

        if self.video and (percent - self.video.percent_complete) < 1 and not video_done and not video_changed and not video_error:
            return

        self.video = VideoFile.objects.get(pk=videofile.pk)

        try:
            if self.video.cancel_download:
                raise DownloadCancelled()

            else:
                if video_error:
                    self.video.percent_complete = 0
                    self.video.save()
                    return

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
                video_node = get_video_node_by_youtube_id(self.video.youtube_id)
                video_title = (video_node and _(video_node["title"])) or self.video.youtube_id

                # Calling update_stage, instead of next_stage when stage changes, will auto-call next_stage appropriately.
                self.update_stage(stage_name=self.video.youtube_id, stage_percent=percent/100., notes=_("Downloading '%(video_title)s'") % {"video_title": _(video_title)})

                if percent == 100:
                    self.video = None

        except DownloadCancelled as de:
            if self.video:
                self.stdout.write(_("Download cancelled!") + "\n")

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
                    self.stdout.write(_("Nothing to download; exiting.") + "\n")
                    break

                # Grab a video as OURS to handle, set fields to indicate to others that we're on it!
                # Update the video logging
                video = videos[0]
                video.download_in_progress = True
                video.percent_complete = 0
                video.save()
                self.stdout.write((_("Downloading video '%(youtube_id)s'...") + "\n") % {"youtube_id": video.youtube_id})

                # Update the progress logging
                self.set_stages(num_stages=video_count + len(handled_youtube_ids) + len(failed_youtube_ids) + int(options["auto_cache"]))
                if not self.started():
                    self.start(stage_name=video.youtube_id)

                # Initiate the download process
                try:

                    progress_callback = partial(self.download_progress_callback, video)
                    try:
                        # Download via urllib
                        download_video(video.youtube_id, callback=progress_callback)

                    except URLNotFound:
                        # Video was not found on amazon cloud service,
                        #   either due to a KA mistake, or due to the fact
                        #   that it's a dubbed video.
                        #
                        # We can use youtube-dl to get that video!!
                        logging.debug(_("Retrieving youtube video %(youtube_id)s via youtube-dl") % {"youtube_id": video.youtube_id})

                        def youtube_dl_cb(stats, progress_callback, *args, **kwargs):
                            if stats['status'] == "finished":
                                percent = 100.
                            elif stats['status'] == "downloading":
                                percent = 100. * stats['downloaded_bytes'] / stats['total_bytes']
                            else:
                                percent = 0.
                            progress_callback(percent=percent)
                        scrape_video(video.youtube_id, quiet=not settings.DEBUG, callback=partial(youtube_dl_cb, progress_callback=progress_callback))

                    except IOError as e:
                        logging.exception(e)
                        video.download_in_progress = False
                        video.save()
                        failed_youtube_ids.append(video.youtube_id)
                        time.sleep(10)
                        continue

                    # If we got here, we downloaded ... somehow :)
                    handled_youtube_ids.append(video.youtube_id)
                    self.stdout.write(_("Download is complete!") + "\n")

                except DownloadCancelled:
                    # Cancellation event
                    video.percent_complete = 0
                    video.flagged_for_download = False
                    video.download_in_progress = False
                    video.save()
                    failed_youtube_ids.append(video.youtube_id)

                except Exception as e:
                    # On error, report the error, mark the video as not downloaded,
                    #   and allow the loop to try other videos.
                    msg = _("Error in downloading %(youtube_id)s: %(error_msg)s") % {"youtube_id": video.youtube_id, "error_msg": unicode(e)}
                    self.stderr.write("%s\n" % msg)

                    # If a connection error, we should retry.
                    if isinstance(e, DownloadError):
                        connection_error = "[Errno 8]" in e.args[0]
                    elif isinstance(e, IOError) and hasattr(e, "strerror"):
                        connection_error = e.strerror[0] == 8
                    else:
                        connection_error = False

                    video.download_in_progress = False
                    video.flagged_for_download = connection_error  # Any error other than a connection error is fatal.
                    video.save()

                    # Rather than getting stuck on one video, continue to the next video.
                    self.update_stage(stage_status="error", notes=_("%(error_msg)s; continuing to next video.") % {"error_msg": msg})
                    failed_youtube_ids.append(video.youtube_id)
                    continue

            # Update
            self.complete(notes=_("Downloaded %(num_handled_videos)s of %(num_total_videos)s videos successfully.") % {
                "num_handled_videos": len(handled_youtube_ids),
                "num_total_videos": len(handled_youtube_ids) + len(failed_youtube_ids),
            })
            caching.invalidate_all_caches()

        except Exception as e:
            self.cancel(stage_status="error", notes=_("Error: %(error_msg)s") % {"error_msg": e})
            raise
