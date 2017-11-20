import mock
import os
import socket

from django.core.management import call_command

from kalite.topic_tools.content_models import get_content_item,\
    annotate_content_models_by_youtube_id
from kalite.updates.download_track import VideoQueue
from kalite.updates.videos import download_video, delete_downloaded_files,\
    get_video_local_path

from .base import UpdatesTestCase
from requests.exceptions import HTTPError


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
        with self.assertRaises(HTTPError):
            download_video(self.content_unavailable_item.youtube_id)
        self.assertFalse(os.path.exists(
            get_video_local_path(self.content_unavailable_item.youtube_id)
        ))

    @mock.patch("requests.adapters.HTTPAdapter.send")
    def test_network_error(self, requests_get):
        requests_get.side_effect = socket.timeout
        with self.assertRaises(socket.timeout):
            download_video(self.content_unavailable_item.youtube_id)
        self.assertFalse(os.path.exists(
            get_video_local_path(self.content_unavailable_item.youtube_id)
        ))
    
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

    @mock.patch("requests.adapters.HTTPAdapter.send")
    def test_download_command_fallback(self, requests_get):
        """
        Tests that we download via youtube-dl when `requests` module is patched
        to fail.
        """
        requests_get.side_effect = socket.timeout
        queue = VideoQueue()
        queue.add_files({self.real_video.youtube_id: self.real_video.title}, language="en")
        call_command("videodownload")
        self.assertTrue(os.path.exists(
            get_video_local_path(self.real_video.youtube_id)
        ))

    @mock.patch("kalite.updates.videos.get_thumbnail_url")
    @mock.patch("kalite.updates.videos.get_video_url")
    def test_500_download(self, get_thumbnail_url, get_video_url):
        delete_downloaded_files(self.real_video.youtube_id)
        get_thumbnail_url.return_value = "https://httpstat.us/500"
        get_video_url.return_value = "https://httpstat.us/500"
        
        with self.assertRaises(HTTPError):
            download_video(self.real_video.youtube_id)
        
        self.assertFalse(os.path.exists(
            get_video_local_path(self.real_video.youtube_id)
        ))
