import sys
from datetime import datetime  # main.models imports this way, so we have this hacky dependency.

from django.conf import settings; logging = settings.LOG
from django.utils import unittest

from ..models import *
from kalite.testing.base import KALiteTestCase


class UpdatesUnicodeModelsTest(KALiteTestCase):
    
    korean_string = unichr(54392)
    
    def test_unicode_string(self):
        logging.warn("No unicode test for UpdateProgressLog; write one soon!")

        vfile = VideoFile(youtube_id=self.korean_string)
        self.assertNotIn(unicode(vfile), "Bad Unicode data", "VideoFile: Bad conversion to unicode (before saving).")
        vfile.save()
        self.assertNotIn(unicode(vfile), "Bad Unicode data", "VideoFile: Bad conversion to unicode (after saving).")

