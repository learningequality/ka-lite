"""
"""
import os
import shutil
import tempfile
import random

from django.conf import settings
from django.core import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.cache.backends.locmem import LocMemCache

from kalite.testing.base import KALiteTestCase
from kalite.topic_tools.content_models import get_random_content, update_item
from securesync.models import Device


class MainTestCase(KALiteTestCase):

    def __init__(self, *args, **kwargs):
        self.content_root = tempfile.mkdtemp() + "/"

        super(MainTestCase, self).__init__(*args, **kwargs)

    def setUp(self, *args, **kwargs):
        self.setUp_fake_contentroot()
        return super(KALiteTestCase, self).setUp(*args, **kwargs)

    def setUp_fake_contentroot(self):
        """
        Set up a location for the content folder that won't mess with the actual application.
        Because we're using call_command, the value of settings should persist
        into the annotate_content_items command.
        """
        settings.CONTENT_ROOT = self.content_root

    def tearDown(self):
        self.tearDown_fake_contentroot()
        self.tearDown_fake_device()  # nothing to do

    def tearDown_fake_contentroot(self):
        shutil.rmtree(self.content_root)
        #for path in glob.glob(os.path.join(self.content_root, "*.mp4")):
        #    os.remove(path)

    def tearDown_fake_device(self):
        Device.own_device = None

    def create_random_content_file(self):
        """
        Helper function for testing content files.
        """
        content = get_random_content(kinds=["Video"], limit=1)[0]
        youtube_id = content["id"]
        path = content["path"]
        fake_content_file = os.path.join(settings.CONTENT_ROOT, "%s.mp4" % youtube_id)
        with open(fake_content_file, "w") as fh:
            fh.write("")
        update_item(update={"files_complete": 1, "available": True, "size_on_disk": 12}, path=content["path"])
        self.assertTrue(os.path.exists(fake_content_file), "Make sure the content file was created, youtube_id='%s'." % youtube_id)
        return (fake_content_file, content["id"], youtube_id, path)
