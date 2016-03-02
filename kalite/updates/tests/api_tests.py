import json

import os
from django.contrib.auth.models import User
from django.core.management import call_command
from kalite.main.tests.base import MainTestCase
from kalite.testing.base import KALiteTestCase, KALiteClientTestCase
from kalite.testing.client import KALiteClient
from kalite.testing.mixins.django_mixins import CreateAdminMixin
from kalite.testing.mixins.facility_mixins import FacilityMixins
from kalite.testing.mixins.securesync_mixins import CreateZoneMixin
from kalite.topic_tools.content_models import get_content_item
from mock import patch



class TestAdminApiCalls(MainTestCase):
    """
    Test main.api_views that require an admin login
    """
    ADMIN_USERNAME = "testadmin"
    ADMIN_PASSWORD = "password"

    def __init__(self, *args, **kwargs):
        super(TestAdminApiCalls, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        """
        Create a superuser, then log in.  Add a fake video file.
        """
        super(TestAdminApiCalls, self).setUp(*args, **kwargs)

        call_command("createsuperuser", username=self.ADMIN_USERNAME, email="a@b.com", interactive=False)
        admin_user = User.objects.get(username=self.ADMIN_USERNAME)
        admin_user.set_password(self.ADMIN_PASSWORD)
        admin_user.save()

        # Choose, and create, a video
        self.fake_video_file, self.video_id, self.youtube_id, self.path = self.create_random_content_file()

        # login
        self.client = KALiteClient()
        success = self.client.login(username=self.ADMIN_USERNAME, password=self.ADMIN_PASSWORD)
        self.assertTrue(success, "Was not able to login as the admin user")

    def tearDown(self, *args, **kwargs):
        """
        Remove the fake video file.
        """
        super(TestAdminApiCalls, self).tearDown(*args, **kwargs)
        if os.path.exists(self.fake_video_file):
            os.remove(self.fake_video_file)


    def test_delete_non_existing_video(self):
        """
        "Delete" a video through the API that never existed.
        """
        os.remove(self.fake_video_file)
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

        # Delete a video file, make sure
        result = self.client.delete_videos(paths=[self.path])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while deleting the video through the API: %s" % (result.status_code, result.content))
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")


    def test_delete_existing_video_file(self):
        """
        Delete a video through the API, when only the video exists on disk (not as an object)
        """
        self.assertTrue(os.path.exists(self.fake_video_file), "Video file should exist on disk.")

        # Delete a video file, make sure
        result = self.client.delete_videos(paths=[self.path])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while deleting the video through the API: %s" % (result.status_code, result.content))
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")
        videofile = get_content_item(content_id=self.video_id)
        self.assertFalse(videofile.get("available"))
        assert videofile.get("size_on_disk") == 0
        assert videofile.get("files_complete") == 0


class VideoLanguageUpdateTestCase(CreateZoneMixin,
                                 CreateAdminMixin,
                                 FacilityMixins,
                                 KALiteClientTestCase):

    def setUp(self, db=None):
        super(VideoLanguageUpdateTestCase, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

        self.zone = self.create_zone()
        self.device_zone = self.create_device_zone(self.zone)
        self.facility = self.create_facility()

    @patch('kalite.updates.api_views.force_job')
    @patch('kalite.updates.api_views.get_download_youtube_ids', return_value={"test": "this"})
    def test_start_video_download(self, force_job, get_download_youtube_ids):
        self.client.login(username='admin', password='admin')
        lang = "es-ES"
        api_resp = json.loads(self.client.post_json(url_name="start_video_download", data={"paths": "this/here", "lang": lang}).content)
        args, kwargs = get_download_youtube_ids.call_args
        self.assertEqual(kwargs["locale"], lang)

    @patch('kalite.updates.api_views.annotate_content_models_by_youtube_id')
    @patch('kalite.updates.api_views.get_download_youtube_ids', return_value={"test": "this"})
    def test_start_video_delete(self, annotate_content_models_by_youtube_id, get_download_youtube_ids):
        self.client.login(username='admin', password='admin')
        lang = "es-ES"
        api_resp = json.loads(self.client.post_json(url_name="delete_videos", data={"paths": "this/here", "lang": lang}).content)
        args, kwargs = get_download_youtube_ids.call_args
        self.assertEqual(kwargs["language"], lang)

    @patch('kalite.updates.api_views.force_job')
    def test_start_video_scan(self, force_job):
        self.client.login(username='admin', password='admin')
        lang = "es-ES"
        api_resp = json.loads(self.client.post_json(url_name="video_scan", data={"lang": lang}).content)
        args, kwargs = force_job.call_args
        self.assertEqual(kwargs["language"], lang)
