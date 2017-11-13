from .base import UpdatesTestCase
from kalite.updates.videos import download_video, delete_downloaded_files
from fle_utils.internet.download import URLNotFound
from kalite.topic_tools.content_models import get_content_item,\
    annotate_content_models_by_youtube_id
from kalite.updates.download_track import VideoQueue
from django.core.management import call_command


class TestDownload(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def test_simple_download(self):
        # Download a video that exists for real!
        download_video(self.real_video.youtube_id)
        # After downloading the video, annotate the database
        annotate_content_models_by_youtube_id(youtube_ids=[self.real_video.youtube_id])
        # Check that it's been marked available
        updated = get_content_item(content_id=self.real_video.id)
        self.assertTrue(updated['available'])

    def test_download_unavailable(self):
        with self.assertRaises(URLNotFound):
            download_video(self.content_unavailable_item.youtube_id)

    def test_download_command(self):
        delete_downloaded_files(self.real_video.youtube_id)
        # Check that it's been marked unavailable
        updated = get_content_item(content_id=self.real_video.id)
        annotate_content_models_by_youtube_id(youtube_ids=[self.real_video])
        self.assertFalse(updated['available'])
        queue = VideoQueue()
        queue.add_files({self.real_video.youtube_id: self.real_video.title}, language="en")
        call_command("videodownload")
        annotate_content_models_by_youtube_id(youtube_ids=[self.real_video.youtube_id])
        # Check that it's been marked available
        updated = get_content_item(content_id=self.real_video.id)
        self.assertTrue(updated['available'])
