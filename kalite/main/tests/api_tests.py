"""
"""
from ..models import VideoLog
from kalite import i18n
from kalite.facility.models import Facility, FacilityUser
from kalite.testing import KALiteClient, KALiteTestCase


class TestSaveVideoLog(KALiteTestCase):

    ORIGINAL_POINTS = 84
    ORIGINAL_SECONDS_WATCHED = 32
    NEW_POINTS = 32
    NEW_SECONDS_WATCHED = 15
    YOUTUBE_ID = "aNqG4ChKShI"
    VIDEO_ID = i18n.get_video_id(YOUTUBE_ID) or "dummy"
    YOUTUBE_ID2 = "b22tMEc6Kko"
    VIDEO_ID2 = i18n.get_video_id(YOUTUBE_ID2) or "dummy2"
    USERNAME = "testuser"
    PASSWORD = "dummies"

    def setUp(self):
        super(TestSaveVideoLog, self).setUp()
        # create a facility and user that can be referred to in models across tests
        self.facility = Facility(name="Test Facility")
        self.facility.save()
        self.user = FacilityUser(username=self.USERNAME, facility=self.facility)
        self.user.set_password(self.PASSWORD)
        self.user.save()

        # create an initial VideoLog instance so we have something to update later
        self.original_videolog = VideoLog(video_id=self.VIDEO_ID, youtube_id=self.YOUTUBE_ID, user=self.user)
        self.original_videolog.points = self.ORIGINAL_POINTS
        self.original_videolog.total_seconds_watched = self.ORIGINAL_SECONDS_WATCHED
        self.original_videolog.save()

    def test_new_videolog(self):

        # make sure the target video log does not already exist
        videologs = VideoLog.objects.filter(video_id=self.VIDEO_ID2, user__username=self.USERNAME)
        self.assertEqual(videologs.count(), 0, "The target video log to be newly created already exists")

        c = KALiteClient()

        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")

        # save a new video log
        result = c.save_video_log(
            video_id=self.VIDEO_ID2,
            youtube_id=self.YOUTUBE_ID2,
            total_seconds_watched=self.ORIGINAL_SECONDS_WATCHED,
            points=self.NEW_POINTS,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)

        # get a reference to the newly created VideoLog
        videolog = VideoLog.objects.get(video_id=self.VIDEO_ID2, user__username=self.USERNAME)

        # make sure the VideoLog was properly created
        self.assertEqual(videolog.points, self.NEW_POINTS, "The VideoLog's points were not saved correctly.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED, "The VideoLog's seconds watched was not saved correctly.")

    def test_update_videolog(self):

        # get a new reference to the existing VideoLog
        videolog = VideoLog.objects.get(id=self.original_videolog.id)

        # make sure the VideoLog hasn't already been changed
        self.assertEqual(videolog.points, self.ORIGINAL_POINTS, "The VideoLog's points have already changed.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED, "The VideoLog's seconds watched already changed.")

        c = KALiteClient()

        # login
        success = c.login(username=self.USERNAME, password=self.PASSWORD, facility=self.facility.id)
        self.assertTrue(success, "Was not able to login as the test user")

        # save a new record onto the video log, with a correct answer (increasing the points and streak)
        result = c.save_video_log(
            video_id=self.VIDEO_ID,
            youtube_id=self.YOUTUBE_ID,
            total_seconds_watched=self.ORIGINAL_SECONDS_WATCHED + self.NEW_SECONDS_WATCHED,
            points=self.ORIGINAL_POINTS + self.NEW_POINTS,
        )
        self.assertEqual(result.status_code, 200, "An error (%d) was thrown while saving the video log." % result.status_code)

        # get a reference to the updated VideoLog
        videolog = VideoLog.objects.get(video_id=self.VIDEO_ID, user__username=self.USERNAME)

        # make sure the VideoLog was properly updated
        self.assertEqual(videolog.points, self.ORIGINAL_POINTS + self.NEW_POINTS, "The VideoLog's points were not updated correctly.")
        self.assertEqual(videolog.total_seconds_watched, self.ORIGINAL_SECONDS_WATCHED + self.NEW_SECONDS_WATCHED, "The VideoLog's seconds watched was not updated correctly.")
