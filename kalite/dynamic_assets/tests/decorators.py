from django.test import TestCase

from ..decorators import dynamic_settings
from ..models import DynamicSettings


class DynamicSettingDecoratorTestCase(TestCase):

    def test_decorator_inserts_dynamic_settings(self):

        @dynamic_settings
        def test_view(request, ds):
            self.assertTrue(isinstance(ds, DynamicSettings))

        test_view(None)
