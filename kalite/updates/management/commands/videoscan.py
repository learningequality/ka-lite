import glob
import time
from annoying.functions import get_object_or_None
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

import settings
from shared import caching, i18n
from shared.videos import download_video
from updates.models import VideoFile
from utils.general import break_into_chunks


class Command(BaseCommand):
    help = "Sync up the database's version of what videos have been downloaded with the actual folder contents"

    option_list = BaseCommand.option_list + (
        make_option('-c', '--cache',
            action='store_true',
            dest='auto_cache',
            default=False,
            help='Create cached files',
            metavar="AUTO_CACHE"),
    )

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("videoscan should be run on the distributed server only.")

        caching_enabled = (settings.CACHE_TIME != 0)
        touched_video_ids = []

        # delete VideoFile objects that are not marked as in progress, but are neither 0% nor 100% done; they're broken
        video_files_to_delete = VideoFile.objects.filter(download_in_progress=False, percent_complete__gt=0, percent_complete__lt=100)
        youtube_ids_to_delete = [d["youtube_id"] for d in video_files_to_delete.values("youtube_id")]
        video_files_to_delete.delete()
        touched_video_ids += [i18n.get_video_id(yid) for yid in youtube_ids_to_delete]
        if len(video_files_to_delete):
            self.stdout.write("Deleted %d VideoFile models (to mark them as not downloaded, since they were in a bad state)\n" % len(video_files_to_delete))

        files = glob.glob(settings.CONTENT_ROOT + "*.mp4")
        videos_marked_at_all = set([video.youtube_id for video in VideoFile.objects.all()])
        videos_marked_as_in_progress = set([video.youtube_id for video in VideoFile.objects.filter(download_in_progress=True)])
        videos_marked_as_unstarted = set([video.youtube_id for video in VideoFile.objects.filter(percent_complete=0, download_in_progress=False)])

        videos_flagged_for_download = set([video.youtube_id for video in VideoFile.objects.filter(flagged_for_download=True)])
        videos_in_filesystem = set([path.replace("\\", "/").split("/")[-1].split(".")[0] for path in files])

        # Files that exist, but are not in the DB, should be assumed to be good videos,
        #   and just needing to be added to the DB.  Add them to the DB in this way,
        #   so that these files also trigger the update code below (and trigger cache invalidation)
        video_ids_needing_model_creation = list(videos_in_filesystem - videos_marked_at_all)
        count = len(video_ids_needing_model_creation)
        if count:
            # OK to do bulk_create; cache invalidation triggered via save download
            VideoFile.objects.bulk_create([VideoFile(youtube_id=id, percent_complete=100, download_in_progress=False) for id in video_ids_needing_model_creation])
            self.stdout.write("Created %d VideoFile models (and marked them as complete, since the files exist)\n" % len(video_ids_needing_model_creation))
            touched_video_ids += [i18n.get_video_id(yid) or yid for yid in video_ids_needing_model_creation]
            for video in video_ids_needing_model_creation:
                caching.invalidate_on_video_update(sender=self.handle, instance=VideoFile.objects.get(youtube_id=video))

        # Files that exist, are in the DB, but have percent_complete=0, download_in_progress=False
        #   These should be individually saved to be 100% complete, to trigger their availability (and cache invalidation)
        count = 0
        for chunk in break_into_chunks(videos_in_filesystem):
            video_files_needing_model_update = VideoFile.objects.filter(percent_complete=0, download_in_progress=False, youtube_id__in=chunk)
            count += video_files_needing_model_update.count()
            video_files_needing_model_update.update(percent_complete=100, flagged_for_download=False)
            for video in video_files_needing_model_update:
                caching.invalidate_on_video_update(sender=self.handle, instance=VideoFile.objects.get(youtube_id=video))

        if count:
            self.stdout.write("Updated %d VideoFile models (to mark them as complete, since the files exist)\n" % count)

        # VideoFile objects say they're available, but that don't actually exist.
        count = 0
        videos_needing_model_deletion_chunked = break_into_chunks(videos_marked_at_all - videos_in_filesystem - videos_flagged_for_download)
        for chunk in videos_needing_model_deletion_chunked:
            video_files_needing_model_deletion = VideoFile.objects.filter(youtube_id__in=chunk)
            count += video_files_needing_model_deletion.count()
            video_files_needing_model_deletion.delete()
            touched_video_ids += [i18n.get_video_id(yid) or yid for yid in chunk]
        if count:
            self.stdout.write("Deleted %d VideoFile models (because the videos didn't exist in the filesystem)\n" % count)

        if options["auto_cache"] and caching_enabled and touched_video_ids:
            caching.regenerate_all_pages_related_to_videos(video_ids=list(set(touched_video_ids)))
