import sys

from django.utils import unittest

from central.models import *
from utils.testing.unicode import UnicodeModelsTest

class CentralUnicodeModelsTest(UnicodeModelsTest):

    @unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
    def test_unicode_class_coverage(self):
        # Make sure we're testing all classes
        self.check_unicode_class_coverage(
            models_module="central.models",
            known_classes = [Organization, UserProfile],
        )


    def test_unicode_string(self):
        #   NOTE: we're not testing UserProfile

        # Stand-alone classes
        org = Organization(
            name=self.korean_string,
            description=self.korean_string,
            number=self.korean_string,
            address=self.korean_string,
            country=self.korean_string,
        )
        self.assertNotIn(unicode(org), "Bad Unicode data", "Organization: Bad conversion to unicode.")
