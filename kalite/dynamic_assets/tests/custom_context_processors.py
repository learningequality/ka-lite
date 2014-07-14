from django.template import RequestContext, Template
from django.test import client, TestCase
from django.test.utils import override_settings

from ..finder import all_dynamic_settings


@override_settings(INSTALLED_APPS=['kalite.dynamic_assets.tests.test_app'])
class ContextProcessorTests(TestCase):

    def setUp(self):
        self.factory = client.RequestFactory()

    def test_dynamic_settings_available_in_templates(self):
        s = all_dynamic_settings()
        request = self.factory.get('/')
        request.session = {}    # factory doesn't run middleware?

        t = Template("{{ TEST_TEXT }}")
        rendered = t.render(RequestContext(request))

        self.assertEquals(rendered, s['TEST_TEXT'])
