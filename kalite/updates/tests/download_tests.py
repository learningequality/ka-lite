from .base import UpdatesTestCase
from kalite.updates.videos import download_video
from fle_utils.internet.download import URLNotFound


class TestDownload(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def test_simple_download(self):
        download_video(self.real_video.youtube_id)

    def test_download_unavailable(self):
        with self.assertRaises(URLNotFound):
            download_video(self.content_unavailable_item.youtube_id)
