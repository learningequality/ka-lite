from django.test import TestCase

from ..decorators import dynamic_settings
from .. import DynamicSettingsBase


class DynamicSettingDecoratorTestCase(TestCase):

    def test_decorator_inserts_dynamic_settings(self):

        @dynamic_settings
        def test_view(request, ds):
            self.assertTrue(isinstance(ds, dict))
            self.assertTrue(isinstance(ds.values()[0], DynamicSettingsBase))

        test_view(None)
