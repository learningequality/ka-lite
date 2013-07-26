import sys

from django.utils import unittest

from central.models import *
from utils.testing.general import all_classes_in_module


@unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
class UnicodeModelsTest(unittest.TestCase):
    korean_string = unichr(54392)

    def test_unicode_string(self):

        # Make sure we're testing all classes
        #   NOTE: we're not testing UserProfile
        found_classes = filter(lambda class_obj: "__unicode__" in dir(class_obj), all_classes_in_module("central.models"))
        known_classes = [Organization, UserProfile]
        self.assertTrue(not set(found_classes) - set(known_classes), "test for unknown classes in the module.")

        # Stand-alone classes
        org = Organization(
            name=self.korean_string,
            description=self.korean_string,
            number=self.korean_string,
            address=self.korean_string,
            country=self.korean_string,
        )
        self.assertNotIn(unicode(org), "Bad Unicode data", "Organization: Bad conversion to unicode.")
