from mock import patch

from django.core.management import call_command
from django.db.models.signals import post_save

from kalite.testing.base import KALiteTestCase
from kalite.updates.models import VideoFile
from kalite import updates, caching

class CacheInvalidationTestCase(KALiteTestCase):
    """
    Test that cache invalidation only happens ONCE per videoscan, even if multiple deletions are made.
    See issue 3621.
    """

    def setUp(self):
        super(CacheInvalidationTestCase, self).setUp()
        # Depends on the implementation details of videoscan command
        # Youtube id should be not None so that these videos are in the `videos_marked_at_all` set.
        # Since they don't actually exist they should automatically fail to be in `youtube_ids_in_filesystem` set.
        # `flagged_for_download=False` ensures `delete_objects_for_missing_videos` function attempts to delete them.
        # `percent_complete=100` ensures that the listener does something nontrivial.
        post_save.disconnect(receiver=updates.invalidate_on_video_update, sender=VideoFile)
        VideoFile.objects.create(youtube_id="blah1", flagged_for_download=False, percent_complete=100)
        VideoFile.objects.create(youtube_id="blah2", flagged_for_download=False, percent_complete=100)
        post_save.connect(receiver=updates.invalidate_on_video_update, sender=VideoFile)

    @patch('kalite.caching.invalidate_all_caches')
    def test_cache_invaldation_occurs_exactly_once(self, mock_func):
        call_command("videoscan")
        actual = mock_func.call_count
        self.assertEqual(actual, 1, "The call count should be exactly 1. Actual count: {actual}".format(actual=actual))

