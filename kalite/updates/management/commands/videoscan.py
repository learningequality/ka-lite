"""
"""
import glob
import os
from optparse import make_option

from django.db.models.signals import pre_delete
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...api_views import divide_videos_by_language
from ...models import VideoFile
from fle_utils.chronograph.management.croncommand import CronCommand
from fle_utils.general import break_into_chunks
from kalite import caching, i18n
from kalite import updates


class Command(CronCommand):
    help = "Sync up the database's version of what videos have been downloaded with the actual folder contents"

    unique_option_list = (
        make_option('-c', '--cache',
            action='store_true',
            dest='auto_cache',
            default=False,
            help='Create cached files',
            metavar="AUTO_CACHE"),
    )

    option_list = CronCommand.option_list + unique_option_list

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("videoscan should be run on the distributed server only.")

        caching_enabled = (settings.CACHE_TIME != 0)
        touched_video_ids = []

        # Filesystem
        files = glob.glob(os.path.join(settings.CONTENT_ROOT, "*.mp4"))
        youtube_ids_in_filesystem = set([os.path.splitext(os.path.basename(f))[0] for f in files])

        # Database
        videos_marked_at_all = set([video.youtube_id for video in VideoFile.objects.all()])

        def delete_objects_for_incomplete_videos():
            # delete VideoFile objects that are not marked as in progress, but are neither 0% nor 100% done; they're broken
            video_files_to_delete = VideoFile.objects.filter(download_in_progress=False, percent_complete__gt=0, percent_complete__lt=100)
            deleted_video_ids = [i18n.get_video_id(video_file.youtube_id) for video_file in video_files_to_delete]
            video_files_to_delete.delete()
            if deleted_video_ids:
                self.stdout.write("Deleted %d VideoFile models (to mark them as not downloaded, since they were in a bad state)\n" % len(deleted_video_ids))
            return deleted_video_ids
        touched_video_ids += delete_objects_for_incomplete_videos()


        def add_missing_objects_to_db(youtube_ids_in_filesystem, videos_marked_at_all):
            # Files that exist, but are not in the DB, should be assumed to be good videos,
            #   and just needing to be added to the DB.  Add them to the DB in this way,
            #   so that these files also trigger the update code below (and trigger cache invalidation)
            youtube_ids_needing_model_creation = list(youtube_ids_in_filesystem - videos_marked_at_all)
            new_video_files = []
            if youtube_ids_needing_model_creation:
                for lang_code, youtube_ids in divide_videos_by_language(youtube_ids_needing_model_creation).iteritems():
                    # OK to do bulk_create; cache invalidation triggered via save download
                    lang_video_files = [VideoFile(youtube_id=id, percent_complete=100, download_in_progress=False, language=lang_code) for id in youtube_ids]
                    VideoFile.objects.bulk_create(lang_video_files)
                    new_video_files += lang_video_files
                self.stdout.write("Created %d VideoFile models (and marked them as complete, since the files exist)\n" % len(new_video_files))

            return [i18n.get_video_id(video_file.youtube_id) for video_file in new_video_files]

        touched_video_ids += add_missing_objects_to_db(youtube_ids_in_filesystem, videos_marked_at_all)

        def update_objects_to_be_complete(youtube_ids_in_filesystem):
            # Files that exist, are in the DB, but have percent_complete=0, download_in_progress=False
            updated_video_ids = []
            for chunk in break_into_chunks(youtube_ids_in_filesystem):
                video_files_needing_model_update = VideoFile.objects.filter(percent_complete=0, download_in_progress=False, youtube_id__in=chunk)
                video_files_needing_model_update.update(percent_complete=100, flagged_for_download=False)

                updated_video_ids += [i18n.get_video_id(video_file.youtube_id) for video_file in video_files_needing_model_update]

            if updated_video_ids:
                self.stdout.write("Updated %d VideoFile models (to mark them as complete, since the files exist)\n" % len(updated_video_ids))
            return updated_video_ids
        touched_video_ids += update_objects_to_be_complete(youtube_ids_in_filesystem)

        def delete_objects_for_missing_videos(youtube_ids_in_filesystem, videos_marked_at_all):
            # VideoFile objects say they're available, but that don't actually exist.
            deleted_video_ids = []
            videos_flagged_for_download = set([video.youtube_id for video in VideoFile.objects.filter(flagged_for_download=True)])
            videos_needing_model_deletion_chunked = break_into_chunks(videos_marked_at_all - youtube_ids_in_filesystem - videos_flagged_for_download)
            # Disconnect cache-invalidation listener to prevent it from being called multiple times
            for chunk in videos_needing_model_deletion_chunked:
                video_files_needing_model_deletion = VideoFile.objects.filter(youtube_id__in=chunk)
                deleted_video_ids += [video_file.youtube_id for video_file in video_files_needing_model_deletion]
                video_files_needing_model_deletion.delete()
            if deleted_video_ids:
                caching.invalidate_all_caches()
                self.stdout.write("Deleted %d VideoFile models (because the videos didn't exist in the filesystem)\n" % len(deleted_video_ids))
            return deleted_video_ids

        touched_video_ids += delete_objects_for_missing_videos(youtube_ids_in_filesystem, videos_marked_at_all)

        if options["auto_cache"] and touched_video_ids:
            caching.invalidate_all_caches()
