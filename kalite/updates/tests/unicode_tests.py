import sys
from datetime import datetime  # main.models imports this way, so we have this hacky dependency.

from django.conf import settings; logging = settings.LOG
from django.utils import unittest

from ..models import *
from fle_utils.testing import UnicodeModelsTest
from kalite.facility.models import Facility, FacilityGroup, FacilityUser
from kalite.testing import KALiteTestCase


class UpdatesUnicodeModelsTest(KALiteTestCase, UnicodeModelsTest):

    @unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
    def test_unicode_class_coverage(self):
        # Make sure we're testing all classes
        self.check_unicode_class_coverage(
            models_module="updates.models",
            known_classes = [UpdateProgressLog, VideoFile],
        )


    def test_unicode_string(self):
        logging.warn("No unicode test for UpdateProgressLog; write one soon!")

        vfile = VideoFile(youtube_id=self.korean_string)
        self.assertNotIn(unicode(vfile), "Bad Unicode data", "VideoFile: Bad conversion to unicode (before saving).")
        vfile.save()
        self.assertNotIn(unicode(vfile), "Bad Unicode data", "VideoFile: Bad conversion to unicode (after saving).")

