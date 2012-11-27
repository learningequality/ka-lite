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
        files = glob.glob(settings.VIDEO_PATH + "*.mp4")
        existing_videos = set([path.replace("\\", "/").split("/")[-1].split(".")[0] for path in files])
        marked_videos = set([video.youtube_id for video in VideoFile.objects.filter(percent_complete=100)])
        partial_videos = set([video.youtube_id for video in VideoFile.objects.filter(download_in_progress=True)])
        
        new_videos = existing_videos - marked_videos - partial_videos
        deleted_videos = marked_videos - existing_videos
        
        for youtube_id in new_videos:
            video = get_object_or_None(VideoFile, youtube_id=youtube_id) or VideoFile(youtube_id=youtube_id)
            if video.download_in_progress or video.percent_complete == 100:
                continue
            video.percent_complete = 100
            video.flagged_for_download = False
            video.save()
            # print "Marked %s as complete." % youtube_id
        
        for youtube_id in deleted_videos:
            video = get_object_or_None(VideoFile, youtube_id=youtube_id)
            if not video:
                continue
            video.delete()
            # print "Deleted %s." % youtube_id
