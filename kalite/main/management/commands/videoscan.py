import time, glob
from django.core.management.base import BaseCommand, CommandError
from annoying.functions import get_object_or_None
from kalite.main.models import VideoFile
from kalite.utils.videos import download_video
from utils.jobs import force_job

import settings


class Command(BaseCommand):
    help = "Sync up the database's version of what videos have been downloaded with the actual folder contents"

    def handle(self, *args, **options):

        # delete VideoFile objects that are not marked as in progress, but are neither 0% nor 100% done; they're broken
        VideoFile.objects.filter(download_in_progress=False, percent_complete__gt=0, percent_complete__lt=100).delete()

        files = glob.glob(settings.VIDEO_PATH + "*.mp4")
        videos_marked_at_all = set([video.youtube_id for video in VideoFile.objects.all()])
        videos_marked_as_in_progress = set([video.youtube_id for video in VideoFile.objects.filter(download_in_progress=True)])
        videos_marked_as_unstarted = set([video.youtube_id for video in VideoFile.objects.filter(percent_complete=0, download_in_progress=False)])
        
        max_vars = 500
        videos_in_filesystem = set([path.replace("\\", "/").split("/")[-1].split(".")[0] for path in files])
        videos_in_filesystem_list = list(videos_in_filesystem)
        videos_in_filesystem_chunked = [videos_in_filesystem_list[i*max_vars:(i+1)*max_vars] for i in range(0, len(videos_in_filesystem_list), max_vars)]
        
        for chunk in videos_in_filesystem_chunked:
            video_files_needing_model_update = VideoFile.objects.filter(percent_complete=0, download_in_progress=False, youtube_id__in=chunk)
            print "Updating %d models" % video_files_needing_model_update.count()
            video_files_needing_model_update.update(percent_complete=100, flagged_for_download=False)
        
        video_ids_needing_model_creation = list(videos_in_filesystem - videos_marked_at_all)
        print "Creating %d models" % len(video_ids_needing_model_creation)
        VideoFile.objects.bulk_create([VideoFile(youtube_id=youtube_id, percent_complete=100) for youtube_id in video_ids_needing_model_creation])
        
        for chunk in videos_in_filesystem_chunked:
            video_files_needing_model_deletion = VideoFile.objects.filter(percent_complete=100).exclude(youtube_id__in=chunk)
            print "Deleting %d models" % video_files_needing_model_update.count()
            video_files_needing_model_deletion.delete()
        
        # for youtube_id in new_video_files_needing_model:
        #     video = get_object_or_None(VideoFile, youtube_id=youtube_id) or VideoFile(youtube_id=youtube_id)
        #     video.percent_complete = 100
        #     video.flagged_for_download = False
        #     video.save()
        #     # print "Marked %s as complete." % youtube_id
        
        # for youtube_id in deleted_videos:
        #     video = get_object_or_None(VideoFile, youtube_id=youtube_id)
        #     if not video:
        #         continue
        #     video.delete()
        #     # print "Deleted %s." % youtube_id
