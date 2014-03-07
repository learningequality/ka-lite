from django.utils import unittest

from .general import all_classes_in_module


class UnicodeModelsTest(unittest.TestCase):
    korean_string = unichr(54392)

    def check_unicode_class_coverage(self, models_module, known_classes):

        # Make sure we're testing all classes
        #   NOTE: we're not testing UserProfile
        found_classes = filter(lambda class_obj: hasattr(class_obj, "__unicode__"), all_classes_in_module(models_module))
        self.assertTrue(not set(found_classes) - set(known_classes), "The following models have __unicode__ methods that need to have tests written: %s" % ", ".join([str(cls) for cls in set(found_classes) - set(known_classes)]))

