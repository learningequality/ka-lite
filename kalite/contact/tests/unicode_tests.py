import sys

from django.utils import unittest

from contact.models import *
from testing.unicode import UnicodeModelsTest

class ContactUnicodeModelsTest(UnicodeModelsTest):

    @unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
    def test_unicode_class_coverage(self):
        # Make sure we're testing all classes
        self.check_unicode_class_coverage(
            models_module="contact.models",
            known_classes = [Contact, Contribute, Deployment, Info, Support],
        )


    def test_unicode_string(self):
        # Stand-alone classes
        contact = Contact(name=self.korean_string, type=self.korean_string, org_name=self.korean_string)
        self.assertNotIn(unicode(contact), "Bad Unicode data", "Contact: Bad conversion to unicode.")

        # Classes using other classes
        dep = Deployment(
            contact=contact,
            countries=self.korean_string,
            facilities=self.korean_string,
            low_cost_bundle=self.korean_string,
            other=self.korean_string,
        )
        self.assertNotIn(unicode(dep), "Bad Unicode data", "Deployment: Bad conversion to unicode.")

        supp = Support(
            contact=contact,
            type=self.korean_string,
            issue=self.korean_string,
        )
        self.assertNotIn(unicode(supp), "Bad Unicode data", "Support: Bad conversion to unicode.")

        contrib = Contribute(
            contact=contact,
            type=self.korean_string,
            issue=self.korean_string,
        )
        self.assertNotIn(unicode(contrib), "Bad Unicode data", "Contribute: Bad conversion to unicode.")

        info = Info(
            contact=contact,
            issue=self.korean_string,
        )
        self.assertNotIn(unicode(info), "Bad Unicode data", "Info: Bad conversion to unicode.")
