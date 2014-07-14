from django.test.utils import override_settings
from django.conf import settings
from django.test import TestCase

from ..finder import all_dynamic_settings, _dynamic_settings

@override_settings(INSTALLED_APPS=['kalite.dynamic_assets.tests.test_app'])
class DynamicSettingsFindersTests(TestCase):

    # functions tested by this test case

    def test_find_test_module_settings(self):

        from .test_app.dynamic_settings import DynamicSettings as settings

        self.assertEquals(settings, _dynamic_settings('kalite.dynamic_assets.tests.test_app'))

    def test_return_none_when_no_dynamic_settings(self):
        self.assertIsNone(_dynamic_settings('os'))

    def test_return_dict_with_settings(self):
        s = all_dynamic_settings()

        self.assertTrue(s['TEST_URL'])
        self.assertTrue(s['IS_FAKE'])
        self.assertTrue('not_a_setting' not in s)

    @override_settings(DYNAMIC_SETTINGS_PRIORITY_APPS=['kalite.dynamic_assets.tests.test_app_2'])
    def test_priority_apps_always_overrides_settings(self):
        s = all_dynamic_settings()

        self.assertTrue(s['IS_OVERRIDEN'])
