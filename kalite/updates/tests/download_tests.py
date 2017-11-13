from .base import UpdatesTestCase
from kalite.updates.videos import download_video
from fle_utils.internet.download import URLNotFound
from kalite.topic_tools.content_models import get_content_item,\
    annotate_content_models_by_youtube_id


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
