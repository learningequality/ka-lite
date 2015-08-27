import os

from django.contrib.auth.models import User
from django.core.management import call_command

from ..models import VideoFile
from kalite.main.tests.base import MainTestCase
from kalite.testing.client import KALiteClient


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
        self.fake_video_file, self.video_id, self.youtube_id = self.create_random_content_file()
        self.assertEqual(VideoFile.objects.all().count(), 0, "Make sure there are no VideoFile objects, to start.")

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
        result = self.client.delete_videos(youtube_ids=[self.youtube_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while deleting the video through the API: %s" % (result.status_code, result.content))
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

    def test_delete_existing_video_object(self):
        """
        Delete a video through the API, when only the videofile object exists
        """
        VideoFile(youtube_id=self.youtube_id).save()
        os.remove(self.fake_video_file)
        self.assertEqual(VideoFile.objects.all().count(), 1, "Should have 1 object; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")

        # Delete a video file, make sure
        result = self.client.delete_videos(youtube_ids=[self.youtube_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while deleting the video through the API: %s" % (result.status_code, result.content))
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have 0 objects; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")


    def test_delete_existing_video_file(self):
        """
        Delete a video through the API, when only the video exists on disk (not as an object)
        """
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertTrue(os.path.exists(self.fake_video_file), "Video file should exist on disk.")

        # Delete a video file, make sure
        result = self.client.delete_videos(youtube_ids=[self.youtube_id])
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while deleting the video through the API: %s" % (result.status_code, result.content))
        self.assertEqual(VideoFile.objects.all().count(), 0, "Should have zero objects; found %d" % VideoFile.objects.all().count())
        self.assertFalse(os.path.exists(self.fake_video_file), "Video file should not exist on disk.")