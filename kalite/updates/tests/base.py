import random

from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import set_database, Item
from peewee import Using


# Some small videos from the content database 2017-11-13
TEST_YOUTUBE_IDS = ["riXcZT2ICjA", "_7aUxFzTG5w"]


@set_database
def add_test_content_videos(instance, db):
    
    youtube_id = random.choice(TEST_YOUTUBE_IDS)
    
    with Using(db, [Item], with_transaction=False):
        real_video = Item.create(
            title="A real video from KA/Youtube",
            description="This video exists",
            available=False,
            kind="Video",
            id=youtube_id,
            youtube_id=youtube_id,
            slug="youtube-vid",
            path=instance.content_unavailable_content_path,
            parent=random.choice(instance.content_subsubtopics).pk,
        )
        instance.real_video = real_video
        instance.content_videos.append(real_video)


class UpdatesTestCase(KALiteTestCase):
    """
    Generic setup / teardown for updates tests
    """
    def setUp(self):
        super(UpdatesTestCase, self).setUp()
        add_test_content_videos(self)
