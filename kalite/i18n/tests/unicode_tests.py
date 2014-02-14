import sys
from datetime import datetime  # main.models imports this way, so we have this hacky dependency.

from django.utils import unittest

import settings
import version
from facility.models import Facility, FacilityGroup, FacilityUser
from i18n.models import *
from settings import LOG as logging
from testing import KALiteTestCase, UnicodeModelsTest

class i18nUnicodeModelsTest(KALiteTestCase, UnicodeModelsTest):

    @unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
    def test_unicode_class_coverage(self):
        # Make sure we're testing all classes
        self.check_unicode_class_coverage(
            models_module="i18n.models",
            known_classes = [LanguagePack],
        )


    def test_unicode_string(self):
        lpack = LanguagePack(code=self.korean_string, name=self.korean_string, software_version=version.VERSION)
        self.assertNotIn(unicode(lpack), "Bad Unicode data", "LanguagePack: Bad conversion to unicode (before saving).")
        lpack.save()
        self.assertNotIn(unicode(lpack), "Bad Unicode data", "LanguagePack: Bad conversion to unicode (after saving).")
